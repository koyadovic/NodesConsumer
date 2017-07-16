import requests
from requests.auth import HTTPBasicAuth

import json
import subprocess

from tkinter import *
from tkinter import ttk

USER = ''
PW = ''
BROWSER = r'/usr/bin/google-chrome'

AUTH = HTTPBasicAuth(username=USER, password=PW)


class GenericNode(object):
    _node_type = None
    BASE_URL = "http://127.0.0.1:8000/"
    BASE_NODES_URL = "{}api/v1/procedures/nodes/bases/".format(BASE_URL)
    NODE_TYPE_CONDITIONAL = "ConditionalNode"
    NODE_TYPE_MANAGEMENT = "ManagementEntityNode"
    NODE_TYPE_PROCEDURE = "ProcedureDescriptionNode"
    NODE_TYPE_BASE = "BaseNode"
    NODE_TYPES = (
        NODE_TYPE_CONDITIONAL,
        NODE_TYPE_MANAGEMENT,
        NODE_TYPE_PROCEDURE,
        NODE_TYPE_BASE,
    )
    NODE_URLS = {
        NODE_TYPE_CONDITIONAL: "{}api/v1/procedures/nodes/conditionals/".format(BASE_URL),
        NODE_TYPE_MANAGEMENT: "{}api/v1/procedures/nodes/management-entities/".format(BASE_URL),
        NODE_TYPE_PROCEDURE: "{}api/v1/procedures/nodes/descriptions/".format(BASE_URL),
        NODE_TYPE_BASE: "{}api/v1/procedures/nodes/bases/".format(BASE_URL),
    }
    ADMIN_NODE_URLS = {
        NODE_TYPE_CONDITIONAL: "{}admin/procedures/conditionalnode/".format(BASE_URL),
        NODE_TYPE_MANAGEMENT: "{}admin/procedures/managemententitynode/".format(BASE_URL),
        NODE_TYPE_PROCEDURE: "{}admin/procedures/proceduredescriptionnode/".format(BASE_URL),
        NODE_TYPE_BASE: "{}admin/procedures/basenode/".format(BASE_URL),
    }
    def _build_fields(self, **kwargs):
        self._fields = []
        for k, v in kwargs.items():
            self._fields.append(k)
            setattr(self, k, v)
    def __init__(self, *args, **kwargs):
        self._build_fields(**kwargs)
    @staticmethod
    def retrieve_node(node_type, id):
        assert node_type in GenericNode.NODE_TYPES
        response = requests.get("{}{}/".format(GenericNode.NODE_URLS[node_type], id), auth=AUTH)
        cls = eval(node_type)
        obj = cls(**response.json())
        return obj
    def save(self):
        if hasattr(self, 'id') and self.id > 0:
            url = "{}{}/".format(GenericNode.NODE_URLS[self.__class__._node_type], self.id)
            obj_dict = {}
            for field in self._fields:
                obj_dict[field] = getattr(self, field)
            response = requests.patch(url, json=obj_dict, auth=AUTH)
        else:
            url = "{}".format(GenericNode.NODE_URLS[self.__class__._node_type])
            obj_dict = {}
            for field in self._fields:
                obj_dict[field] = getattr(self, field)
            response = requests.post(url, json=obj_dict, auth=AUTH)
            print("obj: {}\nresponse: {}".format(obj_dict, response.text))
            self._build_fields(**response.json())
    def remove(self):
        if hasattr(self, 'id') and self.id > 0:
            url = "{}{}/".format(GenericNode.NODE_URLS[self.__class__._node_type], self.id)
            obj_dict = {}
            response = requests.delete(url, json=obj_dict, auth=AUTH)

    def __repr__(self):
        return self.__str__()


class ConditionalNode(GenericNode):
    _node_type = GenericNode.NODE_TYPE_CONDITIONAL
    def __init__(self, *args, **kwargs):
        super(ConditionalNode, self).__init__(*args, **kwargs)
        url = "{}types/{}/".format(
            GenericNode.NODE_URLS[self.__class__._node_type],
            self.conditional_node_type
        )
        response = requests.get(url, json={}, auth=AUTH)
        self.conditional_text = response.json().get('name')

    def __str__(self):
        return "{} {}".format(self.conditional_text, self.value)


class ManagementEntityNode(GenericNode):
    _node_type = GenericNode.NODE_TYPE_MANAGEMENT
    def __str__(self):
        return "{}".format(self.name)


class ProcedureDescriptionNode(GenericNode):
    _node_type = GenericNode.NODE_TYPE_PROCEDURE
    def __str__(self):
        return "{}".format(self.reference)


class BaseNode(GenericNode):
    _node_type = GenericNode.NODE_TYPE_BASE





##################################################


class TreeNode(object):
    def __init__(self, base_node, concrete_node):
        self.base_node = base_node
        self.concrete_node = concrete_node

    def remove(self):
        self.concrete_node.remove()
        self.base_node.remove()

    def __str__(self):
        return str(self.concrete_node)
    def __repr__(self):
        return self.__str__()



def build_tree(parent_id=None, parent_tk_node=None):
    if parent_tk_node is None:
        parent_tk_node = ""

    if parent_id is None:
        request_uri = '{}'.format(GenericNode.BASE_NODES_URL)
    else:
        request_uri = '{}?parent={}'.format(GenericNode.BASE_NODES_URL, parent_id)

    nodes_json = requests.get(request_uri, auth=AUTH).json().get('results')

    for node_json in nodes_json:
        base_node = GenericNode.retrieve_node(
            "BaseNode",
            node_json.get('id', None)
        )
        concrete_node = GenericNode.retrieve_node(
            node_json.get('concrete_type', None),
            node_json.get('concrete_node', None),
        )

        node = TreeNode(base_node, concrete_node)

        tree_child = tree.insert(
            parent_tk_node,
            'end',
            text="{}".format(node),
            open=True,
            tags=(node.concrete_node._node_type)
        )
        setattr(tree, tree_child + "_node_instance", node)
        build_tree(node.base_node.id, tree_child)

        tree.tag_configure(GenericNode.NODE_TYPE_MANAGEMENT, foreground='#ff0000')
        tree.tag_configure(GenericNode.NODE_TYPE_PROCEDURE, foreground='#00AA00')




root = Tk()

style = ttk.Style()
style.configure(".", font=('Helvetica', 15), foreground="white")
style.configure("Treeview", foreground='grey')
style.configure("Treeview.Heading", foreground='green')
style.configure('Treeview', rowheight=40)

root.geometry('{}x{}'.format(800, 600))
root.resizable(width=False, height=False)
root.title("ZMS2 Procedures Configuration")

tree = ttk.Treeview(root, show="tree")
tree.column("#0", width=800)
tree.heading("#0", text="Column A")


def rebuild_entire_tree():
    tree.delete(*tree.get_children())
    tree.pack(side=LEFT, fill=BOTH, expand=YES)
    root_node = tree.insert('', 'end', text='Root', open=True)
    build_tree(parent_id=None, parent_tk_node=root_node)

rebuild_entire_tree()

popup = Menu(root, tearoff=0)

def _get_node_id():
    try:
        print("{}".format(popup.selection))
        base_node_id = int("{}".format(popup.selection['Node']))
    except:
        return None
    return base_node_id


def change_parent():
    node = popup.node_selection
    url = "{}{}/".format(
        GenericNode.ADMIN_NODE_URLS[node.base_node._node_type],
        node.base_node.id
    )
    subprocess.check_call([BROWSER, url])
    print("Cambiando el padre de: {}".format(node))
    rebuild_entire_tree()

def edit_node():
    node = popup.node_selection
    print("Editando el nodo: {}".format(node))

    rebuild_entire_tree()

# TODO aquí nos quedamos
def add_conditional():
    node = popup.node_selection
    base_node = BaseNode()
    base_node.save()
    base_node.parent = node.base_node.id
    base_node.save()
    concrete_node = ConditionalNode(base_node=base_node.id)
    concrete_node.save()
    print("Add Conditional in node: {}".format(node))
    rebuild_entire_tree()

def add_management_entity():
    node = popup.node_selection
    print("Add management entity in node: {}".format(node))
    rebuild_entire_tree()

def add_procedure_description():
    node = popup.node_selection
    print("Add procedure description in node: {}".format(node))
    rebuild_entire_tree()

def remove_node():
    node = popup.node_selection
    print("Deleting node: {}".format(node))
    node.remove()
    rebuild_entire_tree()

def update_tree():
    rebuild_entire_tree()



popup.add_command(label="Refresh", command=update_tree)
popup.add_separator()
popup.add_command(label="Edit", command=edit_node)
popup.add_command(label="Change parent", command=change_parent)
popup.add_separator()
popup.add_command(label="Add Conditional", command=add_conditional)
popup.add_command(label="Add Management Entity", command=add_management_entity)
popup.add_command(label="Add Procedure Description", command=add_procedure_description)
popup.add_separator()
popup.add_command(label="Remove node", command=remove_node)


def do_popup(event):
    # display the popup menu
    try:

        iid = tree.identify_row(event.y)
        if iid:
            # mouse pointer over item
            tree.selection_set(iid)
            node = None
            try:
                node = getattr(tree, iid + "_node_instance")
            except:
                pass

            popup.node_selection = node
            popup.post(event.x_root, event.y_root)
    finally:
        # make sure to release the grab (Tk 8.0a1 only)
        popup.grab_release()


tree.bind("<Button-3>", do_popup)
tree.pack()

root.mainloop()

