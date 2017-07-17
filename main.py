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

    _node_type = None
    _all_fields = []
    _visible_fields = []

    def _build_fields(self, **kwargs):
        for field in set(self._visible_fields + self._all_fields):
            setattr(self, field, "")
        self._all_fields = []
        for k, v in kwargs.items():
            self._all_fields.append(k)
            setattr(self, k, v)
    def __init__(self, *args, **kwargs):
        self._build_fields(**kwargs)
    @staticmethod
    def retrieve_node(node_type, id):
        assert node_type in GenericNode.NODE_TYPES, "Node type: {} not in accepted node types.".format(node_type)
        response = requests.get("{}{}/".format(GenericNode.NODE_URLS[node_type], id), auth=AUTH)
        cls = eval(node_type)
        obj = cls(**response.json())
        return obj
    def save(self):
        print("Metodo save llamado")
        if hasattr(self, 'id') and self.id != "" and int(self.id) > 0:
            url = "{}{}/".format(GenericNode.NODE_URLS[self.__class__._node_type], self.id)
            obj_dict = {}
            for field in self._all_fields:
                obj_dict[field] = getattr(self, field)
            response = requests.patch(url, json=obj_dict, auth=AUTH)
            self._build_fields(**response.json())
            print("Se trata de un elemento ya existente.\nid: {}\nurl: {}\nresponse code: {}".format(self.id, url, response.status_code))
            if response.status_code > 250:
                print("Response text: {}".format(response.text))
        else:
            url = "{}".format(GenericNode.NODE_URLS[self.__class__._node_type])
            obj_dict = {}
            for field in set(self._visible_fields + self._all_fields):
                obj_dict[field] = getattr(self, field)
            response = requests.post(url, json=obj_dict, auth=AUTH)
            print("obj: {}\nresponse: {}".format(obj_dict, response.text))
            self._build_fields(**response.json())
            print("Se trata de un elemento nuevo.\nNuevo id: {}\nurl: {}\nresponse code: {}".format(self.id, url, response.status_code))
            if response.status_code > 250:
                print("Response text: {}".format(response.text))

    def remove(self):
        if hasattr(self, 'id') and self.id > 0:
            url = "{}{}/".format(GenericNode.NODE_URLS[self.__class__._node_type], self.id)
            obj_dict = {}
            response = requests.delete(url, json=obj_dict, auth=AUTH)

    def __str__(self):
        string = ""
        for k in set(self._visible_fields + self._all_fields):
            string += "{}: {} ".format(k, getattr(self, k))
        return string


class ConditionalNode(GenericNode):
    _visible_fields = [
        'conditional_node_type',
        'value',
    ]
    _node_type = GenericNode.NODE_TYPE_CONDITIONAL
    def __init__(self, *args, **kwargs):
        super(ConditionalNode, self).__init__(*args, **kwargs)
        try:
            url = "{}types/{}/".format(
                GenericNode.NODE_URLS[self.__class__._node_type],
                self.conditional_node_type
            )
            response = requests.get(url, json={}, auth=AUTH)
            self.conditional_text = response.json().get('name')
        except:
            self.conditional_text = ""

    def __str__(self):
        return "{} {}".format(self.conditional_text, self.value)


class ManagementEntityNode(GenericNode):
    _visible_fields = [
        'name',
        'address',
        'phone',
        'phone_2',
        'fax',
        'email',
        'url',
    ]
    _node_type = GenericNode.NODE_TYPE_MANAGEMENT
    def __str__(self):
        return "{}".format(self.name)


class ProcedureDescriptionNode(GenericNode):
    _visible_fields = [
        'reference',
        'currency',
        'price_first_copy',
        'price_additional_copies',
    ]
    _node_type = GenericNode.NODE_TYPE_PROCEDURE
    def __str__(self):
        return "{}".format(self.reference)


class BaseNode(GenericNode):
    _visible_fields = [
        'id',
        'parent',
    ]
    _node_type = GenericNode.NODE_TYPE_BASE

    def __str__(self):
        return "Base Node: {}".format(self.id)


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
        concrete_type = node_json.get('concrete_type', None)
        concrete_node = node_json.get('concrete_node', None)
        if concrete_type is not None and concrete_node is not None:
            cnode = GenericNode.retrieve_node(
                concrete_type,
                concrete_node,
            )

            node = TreeNode(base_node, cnode)

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
            tree.tag_configure(GenericNode.NODE_TYPE_PROCEDURE, foreground='#008800')




root = Tk()


class EditorWindow(Toplevel):
    def __init__(self, obj):
        self._obj = obj

        super(EditorWindow, self).__init__(root)
        self.geometry('{}x{}'.format(400, 500))

        frame = Frame(self)

        self._widgets = {}

        for field in obj._visible_fields:
            Label(frame, text=field).pack()
            entry = Entry(frame)
            entry.pack(fill=X)
            entry.insert(0, "{}".format(getattr(obj, field)))
            self._widgets[field] = entry

        Button(frame, command=self.cancel_click, text="Close").pack()
        Button(frame, command=self.save_click, text="Save").pack()

        frame.pack(side=LEFT, fill=BOTH, expand=YES)

    def save_click(self):
        changed = False
        for field in set(self._obj._visible_fields + self._obj._all_fields):
            if field not in self._widgets and getattr(self._obj, field, None) is not None:
                changed = True
                continue
            new_value = self._widgets[field].get()
            if new_value != getattr(self._obj, field):
                setattr(self._obj, field, new_value)
                changed = True

        print("obj: {}".format(self._obj))
        if changed:
            print("Guardandolo, cambio ...")
            self._obj.save()
            rebuild_entire_tree()
        self.destroy()

    def cancel_click(self):
        base_id = getattr(self._obj, 'base_node', None)
        obj_id = getattr(self._obj, 'id', None)
        if base_id is not None and obj_id is None:
            print("Eliminando Nodo base con id: {}".format(base_id))
            base = GenericNode.retrieve_node("BaseNode", base_id)
            base.remove()
        self.destroy()


style = ttk.Style()
style.configure(".", font=('Helvetica', 13), foreground="white")
style.configure("Treeview", foreground='grey')
style.configure("Treeview.Heading", foreground='green')
style.configure('Treeview', rowheight=30)

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


def edit_concrete_node():
    node = popup.node_selection
    EditorWindow(node.concrete_node)
    print("Editando el nodo: {}".format(node.concrete_node))
    rebuild_entire_tree()

def change_parent():
    node = popup.node_selection
    EditorWindow(node.base_node)
    print("Editando el nodo: {}".format(node.base_node))
    rebuild_entire_tree()

def add_conditional():
    node = popup.node_selection
    try:
        base_id = node.base_node.id
    except:
        base_id = None
    base_node = BaseNode(parent=base_id)
    base_node.save()
    EditorWindow(ConditionalNode(base_node=base_node.id))
    print("Add Conditional in node: {}".format(node))

def add_management_entity():
    node = popup.node_selection
    try:
        base_id = node.base_node.id
    except:
        base_id = None
    base_node = BaseNode(parent=base_id)
    base_node.save()
    EditorWindow(ManagementEntityNode(base_node=base_node.id))
    print("Add management entity in node: {}".format(node))
    rebuild_entire_tree()

def add_procedure_description():
    node = popup.node_selection
    try:
        base_id = node.base_node.id
    except:
        base_id = None
    base_node = BaseNode(parent=base_id)
    base_node.save()
    EditorWindow(ProcedureDescriptionNode(base_node=base_node.id))
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
popup.add_command(label="Edit node", command=edit_concrete_node)
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


listbox = Listbox(root)
listbox.pack()

listbox.insert(END, "a list entry")

for item in ["one", "two", "three", "four"]:
    listbox.insert(END, item)




root.mainloop()

