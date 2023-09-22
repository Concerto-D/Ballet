#!/usr/bin/env python
#
# TODO:
# - resource colors:
#     - User-defined using config file.
#     - Automagically chosen from color space.
#     - Advanced algorithm (contact Hannes Pretorius).
# - Koos' specs:
#     - Resources sorted in read-in order (default)
#       or alphabetically (flag).
#     - Have proper gnuplot behavior on windows/x11, eps/pdf, latex terminals.
#     - Create and implement algorithm for critical path analysis.
# - Split generic stuff into a Gantt class, and specific stuff into the main.
#
# gantt.py ganttfile | gnuplot

import itertools, sys, getopt, csv
from configparser import ConfigParser

rectangleHeight = 0.8  #: Height of a rectangle in units.


class Activity(object):
    """
    Container for activity information.

    @ivar resource: Resource name.
    @type resource: C{str}

    @ivar start: Start time of the activity.
    @type start: C{float}

    @ivar stop: End time of the activity.
    @type stop: C{float}
    """

    def __init__(self, resource, start, stop):
        self.resource = resource
        self.start = start
        self.stop = stop


class Rectangle(object):
    """
    Container for rectangle information.
    """

    def __init__(self, bottomleft, topright, fillcolor):
        self.bottomleft = bottomleft
        self.topright = topright
        self.fillcolor = fillcolor
        self.fillstyle = 'solid 0.8'
        self.linewidth = 2


class ColorBook(object):
    """
    Class managing colors.

    @ivar colors
    @ivar palette
    @ivar prefix
    """

    def __init__(self, colorfname, tasks):
        """
        Construct a ColorBook object.

        @param colorfname: Name of the color config file (if specified).
        @type  colorfname: C{str} or C{None}

        @param tasks: Existing task types.
        @type  tasks: C{list} of C{str}
        """
        if colorfname:
            values = self.load_config(colorfname, tasks)
        else:
            values = self.fixed(tasks)

        self.colors, self.palette, self.prefix = values

    def load_config(self, colorfname, tasks):
        """
        Read task colors from a configuration file.
        """
        palettedef = 'model RGB'
        colorprefix = 'rgb'

        # Read in task colors from configuration file
        config = ConfigParser()
        config.optionxform = str  # makes option names case sensitive
        config.readfp(open(colorfname, 'r'))
        # Colors are RGB colornames
        colors = dict(config.items('Colors'))

        # Raise KeyError if no color is specified for a task
        nocolors = [t for t in tasks if t not in colors]
        if nocolors:
            msg = 'Could not find task color for ' + ', '.join(nocolors)
            raise KeyError(msg)

        return colors, palettedef, colorprefix

    def fixed(self, tasks):
        """
        Pick colors from a pre-defined palette.
        """
        # Set task colors
        # SE colors
        # (see http://w3.wtb.tue.nl/nl/organisatie/systems_engineering/\
        #      info_for_se_students/how2make_a_poster/pictures/)
        # Decrease the 0.8 values for less transparent colors.
        se_palette = {"se_red": (1.0, 0.8, 0.8),
                      "se_pink": (1.0, 0.8, 1.0),
                      "se_violet": (0.8, 0.8, 1.0),
                      "se_blue": (0.8, 1.0, 1.0),
                      "se_green": (0.8, 1.0, 0.8),
                      "se_yellow": (1.0, 1.0, 0.8)}
        se_gradient = ["se_red", "se_pink", "se_violet",
                       "se_blue", "se_green", "se_yellow"]
        se_palettedef = '( ' + \
                        ', '.join(('%d ' % n +
                                   ' '.join((str(x) for x in se_palette[c]))
                                   for n, c in enumerate(se_gradient))) + \
                        ' )'

        palettedef = 'model RGB defined %s' % se_palettedef
        colorprefix = 'palette frac'
        # Colors are fractions from the palette defined
        colors = dict((t, '%0.2f' % (float(n) / (len(tasks) - 1)))
                      for n, t in enumerate(tasks))

        return colors, palettedef, colorprefix


class DummyClass(object):
    """
    Dummy class for storing option values in.
    """


def make_rectangles(activities, resource_map, colors):
    """
    Construct a collection of L{Rectangle} for all activities.

    @param activities: Activities being performed.
    @type  activities: C{iterable} of L{Activity}

    @param resource_map: Indices of all resources.
    @type  resource_map: C{dict} of C{str} to C{int}

    @param colors: Colors for all tasks.
    @type  colors: C{dict} of C{str} to C{str}

    @return: Collection of rectangles to draw.
    @rtype:  C{list} of L{Rectangle}
    """
    rectangles = []
    for act in activities:
        ypos = resource_map[act.resource]
        bottomleft = (act.start, ypos - 0.5 * rectangleHeight)
        topright = (act.stop, ypos + 0.5 * rectangleHeight)
        fillcolor = colors[act.resource]
        rectangles.append(Rectangle(bottomleft, topright, fillcolor))

    return rectangles


def load_ganttfile(ganttfile):
    """
    Load the resource/task file.

    @param ganttfile: Name of the gantt file.
    @type  ganttfile: C{str}

    @return: Activities loaded from the file, collection of
             (resource, start, end, task) activities.
    @rtype:  C{list} of L{Activity}
    """
    activities = []
    csvfile = open(ganttfile, 'r')
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in csvreader:
        resource = row[0]
        start = float(row[1])
        stop = float(row[2])
        activities.append(Activity(resource, start, stop))

    return activities


def list_to_activities(tuple_list):
    activities = []
    for (resource, start, stop) in tuple_list:
        activities.append(Activity(resource, start, stop))

    return activities


def make_unique_resources(alphasort, activities):
    """
    Construct collections of unique and resource names.

    @param alphasort: Sort resources alphabetically.
    @type  alphasort: C{bool}

    @param activities: Activities to draw.
    @type  activities: C{list} of L{Activity}

    @return: Collections of resources.
    @rtype:  C{list} of C{str}, C{list} of C{str}
    """
    # Create list with unique resources in activity order.
    resources = []
    for act in activities:
        if act.resource not in resources:
            resources.append(act.resource)

    # Sort such that resources appear in alphabetical order
    if alphasort:
        resources.sort()

    # Resources are read from top (y=max) to bottom (y=1)
    resources.reverse()

    return resources


def generate_plotdata(activities, resources, rectangles, options,
                      resource_map, color_book):
    """
    Generate Gnuplot lines.
    """
    xmin = 0
    xmax = max(act.stop for act in activities)
    ymin = 0 + (rectangleHeight / 2)
    ymax = len(resources) + 1 - (rectangleHeight / 2)
    xlabel = 'Data Range'
    ylabel = ''
    title = options.plottitle
    ytics = ''.join(['(',
                     ', '.join(('"%s" %d' % item)
                               for item in resource_map.items()),
                     ')'])
    # outside and 2 characters from the graph
    grid_tics = 'xtics'

    # Set plot dimensions
    plot_dimensions = ['set xrange [%f:%f]' % (xmin, xmax),
                       'set yrange [%f:%f]' % (ymin, ymax),
                       'set autoscale x',  # extends x axis to next tic mark
                       'set xlabel "%s"' % xlabel,
                       'set ylabel "%s"' % ylabel,
                       'set title "%s"' % title,
                       'set ytics %s' % ytics,
                       'unset key',
                       'set grid %s' % grid_tics,
                       'set palette %s' % color_book.palette,
                       'unset colorbox']

    # Generate gnuplot rectangle objects
    plot_rectangles = (' '.join(['set object %d rectangle' % n,
                                 'from %f, %0.1f' % r.bottomleft,
                                 'to %f, %0.1f' % r.topright,
                                 'fillcolor %s %s' % (color_book.prefix,
                                                      r.fillcolor),
                                 'fillstyle solid 0.8'])
                       for n, r in zip(itertools.count(1), rectangles))

    # Generate gnuplot lines
    plot_lines = ['plot ' +
                  ', \\\n\t'.join(' '.join(['-1',
                                            'with lines',
                                            'linecolor %s %s ' % (color_book.prefix,
                                                                  color_book.colors[t]),
                                            'linewidth 6'])
                                  for t in resources)]

    return plot_dimensions, plot_rectangles, plot_lines


def write_data(plot_dimensions, plot_rectangles, plot_lines, fname):
    """
    Write plot data out to file or screen.

    @param fname: Name of the output file, if specified.
    @type  fname: C{str}  (??)
    """
    if fname:
        g = open(fname, 'w')
        g.write('\n'.join(itertools.chain(plot_dimensions, plot_rectangles,
                                          plot_lines)))
        g.close()
    else:
        print('\n'.join(itertools.chain(plot_dimensions, plot_rectangles,
                                        plot_lines)))


def fmt_opt(short, long, arg, text):
    if arg:
        return '-%s %s, --%s%s\t%s' % (short[:-1], arg, long, arg, text)
    else:
        return '-%s, --%s\t%s' % (short, long, text)


def make_default_options():
    option_values = DummyClass()
    option_values.outputfile = ''
    option_values.colorfile = ''
    option_values.alphasort = False
    option_values.plottitle = ''
    return option_values


def process_options():
    """
    Handle option and command-line argument processing.

    @return: Options and gantt input filename.
    @rtype:  L{OptionParser} options, C{str}
    """
    optdefs = [('o:', 'output=', 'FILE', 'Write output to FILE.'),
               ('c:', 'color=', 'FILE', 'Use task colors (RGB) as defined in '
                                        'configuration FILE (in RGB triplets,\n\t\t\t\tGnuplot '
                                        'colornames, or hexadecimal representations.'),
               ('a', 'alpha', '', '\t\tShow resources and tasks in '
                                  'alphabetical order.'),
               ('t:', 'title=', 'TITLE', 'Set plot title to TITLE (between '
                                         'double quotes).'),
               ('h', 'help', '', '\t\tShow online help.')]
    short_opts = ''.join(opt[0] for opt in optdefs if opt[0])
    long_opts = [opt[1] for opt in optdefs if opt[1]]
    usage_text = 'gantt.py [options] gantt-file\nwhere\n' + \
                 '\n'.join('    ' + fmt_opt(*opt) for opt in optdefs)

    option_values = make_default_options()

    try:
        opts, args = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as err:
        sys.stderr.write("gantt.py: %s\n" % err)
        sys.exit(2)

    for opt, optval in opts:
        if opt in ('-o', '--output'):
            option_values.outputfile = optval
            continue
        if opt in ('-c', '--color'):
            option_values.colorfile = optval
            continue
        if opt in ('-a', '--alphasort'):
            option_values.alphasort = True
            continue
        if opt in ('-t', '--title'):
            option_values.plottitle = optval
            continue
        if opt in ('-h', '--help'):
            print(usage_text)
            sys.exit(0)

    # Check if correct number of arguments is supplied
    if len(args) != 1:
        sys.stderr.write('gantty.py: incorrect number of arguments '
                         '(task/resource file expected)\n')
        sys.exit(1)

    return option_values, args[0]


def compute(options, activities):
    resources = make_unique_resources(options.alphasort,
                                      activities)

    # Assign indices to resources
    resource_map = dict(zip(resources, itertools.count(1)))

    color_book = ColorBook(options.colorfile, resources)
    rectangles = make_rectangles(activities, resource_map, color_book.colors)

    plot_dims, plot_rects, plot_lines = \
        generate_plotdata(activities, resources, rectangles,
                          options, resource_map, color_book)

    write_data(plot_dims, plot_rects, plot_lines, options.outputfile)


def compute_from_file(options, ganttfile):
    activities = load_ganttfile(ganttfile)
    compute(options, activities)


def compute_from_list(options, tuple_list):
    activities = list_to_activities(tuple_list)
    compute(options, activities)


def gnuplot_file_from_list(tuple_list, file_name, title=''):
    options = make_default_options()
    options.outputfile = file_name
    options.plottitle = title
    compute_from_list(options, tuple_list)


def run():
    options, ganttfile = process_options()
    compute_from_file(options, ganttfile)


if __name__ == '__main__':
    run()



