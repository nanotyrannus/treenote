class TreeModel:

    class TreeNode:
        def __init__(self, name):
            self.children = []
            self.values = {"name": name}

        def insertChild(self, node):
            if len(self.children) == 0:
                self.children.append(node)
                return 0
            else:
                for i in range(len(self.children)):
                    if node.values['name'] < self.children[i].values['name']:
                        self.children.insert(i, node)
                        return i
                self.children.append(node)
                return len(self.children) - 1
        def __str__(self):
            return self.values['name']

        def printChildren(self):
            for child in self.children:
                print(child)

    class PathException(Exception):
        def __init__(self, message):
            super().__init__(message)

    def __init__(self):
        self.root = self.TreeNode('root')

    def __str__(self):
        return self.traverse(0, self.root)
    
    def traverse(self, level, node, result = ""):
        if len(node.children) == 0:
            return "\t"*level + node.values['name']
        else: 
            result += "\t" * level + node.values['name'] + "\n"
            for n in node.children:
                result += self.traverse(level + 1, n) + '\n'
        return result

    def getItem(self, path):
        # Takes list of strings
        cursor = self.root

        # while len(path) != 0:
        for next in path:
            found = False
            for child in cursor.children:
                if child.values['name'] == next:
                    found = True
                    cursor = child
                    break
            if not found:
                raise Exception("Couldn't insert {} with path {}".format(item, path))
        # print(len(path))
        return cursor

    def insertItem(self, path, item):
        self.getItem(path).insertChild(self.TreeNode(item))

    def insertTopLevelItem(self, item):
        self.root.insertChild(self.TreeNode(item))

    def deleteItem(self, path):
        which = path.pop()
        parent = self.getItem(path)
        for i in range(len(parent.children)):
            if parent.children[i].values['name'] == which:
                if len(parent.children[i].children) == 0:
                    parent.children.pop(i)
                else:
                    raise Exception("Node {} has {} children.".format(parent, len(parent.children)))

    def deleteTopLevelItem(self, item):
        for i in range(len(self.root.children)):
            if self.root.children[i].values['name'] == item:
                self.root.children.pop(i)
                return
