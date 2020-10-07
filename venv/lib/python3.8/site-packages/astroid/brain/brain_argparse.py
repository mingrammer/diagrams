from astroid import MANAGER, arguments, nodes, inference_tip, UseInferenceDefault


def infer_namespace(node, context=None):
    callsite = arguments.CallSite.from_call(node)
    if not callsite.keyword_arguments:
        # Cannot make sense of it.
        raise UseInferenceDefault()

    class_node = nodes.ClassDef("Namespace", "docstring")
    class_node.parent = node.parent
    for attr in set(callsite.keyword_arguments):
        fake_node = nodes.EmptyNode()
        fake_node.parent = class_node
        fake_node.attrname = attr
        class_node.instance_attrs[attr] = [fake_node]
    return iter((class_node.instantiate_class(),))


def _looks_like_namespace(node):
    func = node.func
    if isinstance(func, nodes.Attribute):
        return (
            func.attrname == "Namespace"
            and isinstance(func.expr, nodes.Name)
            and func.expr.name == "argparse"
        )
    return False


MANAGER.register_transform(
    nodes.Call, inference_tip(infer_namespace), _looks_like_namespace
)
