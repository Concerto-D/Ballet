class ClassTag:

    def __init__(self):
        self.tagged_classes = {}

    def tag(self, type_name: str):
        def decorator(cls):
            self.tagged_classes[type_name] = cls
            return cls
        return decorator

    def find_class_by_tag(self, type_name: str):
        res = self.tagged_classes.get(type_name, None)
        if res is None:
            raise ValueError(f"There is no type tagged by {type_name}")
        return res


classtag = ClassTag()
