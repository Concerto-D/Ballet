from ballet.assembly.concertod.dependency import DepType, Dependency


class Connection:
    """
    This class is used by the assembly to store connections between components
    """

    def __init__(self, dep1: Dependency, dep2: Dependency):
        use_dep, provide_dep = self.compute_provide_use_deps(dep1, dep2)
        self._use_dep = use_dep
        self._provide_dep = provide_dep
        self._provide_dep.connect(self)
        self._use_dep.connect(self)

    @property
    def obj_id(self):
        return self.build_id_from_dependencies(self._use_dep, self._provide_dep)

    def to_json(self):
        return {
            "obj_id": self.obj_id
        }

    def can_remove(self) -> bool:
        return not self.is_locked()

    def disconnect(self):
        self._provide_dep.disconnect(self)
        self._use_dep.disconnect(self)

    def get_provide_dep(self) -> Dependency:
        return self._provide_dep

    def get_use_dep(self) -> Dependency:
        return self._use_dep

    def is_active(self) -> bool:
        # If get_nb_users == -1 (the remote dep is not available and there is no cache), consider that it is not active
        return self._provide_dep.get_nb_users() > 0

    def is_locked(self) -> bool:
        # If get_nb_users == -1 (the remote dep is not available and there is no cache), consider that it is locked)
        return self._use_dep.get_nb_users() != 0

    def get_opposite_dependency(self, dep):
        return self._use_dep if dep == self._provide_dep else self._provide_dep

    @staticmethod
    def build_id_from_dependencies(dep1: Dependency, dep2: Dependency):
        use_dep, provide_dep = Connection.compute_provide_use_deps(dep1, dep2)
        return f"{use_dep.obj_id}/{provide_dep.obj_id}"

    @staticmethod
    def compute_provide_use_deps(dep1: Dependency, dep2: Dependency):
        if dep1.get_type() in [DepType.PROVIDE, DepType.DATA_PROVIDE]:
            provide_dep = dep1
            use_dep = dep2
        else:
            provide_dep = dep2
            use_dep = dep1

        return use_dep, provide_dep
