from importlib import import_module
from pathlib import Path

import diagrams
from diagrams import Diagram, Cluster, Edge


def main():
    with Diagram("All Node Types", show=False, outformat='svg'):
        root = Path(diagrams.__file__).parent
        for package_path in sorted(root.iterdir(), reverse=True):
            if package_path.is_dir() and not package_path.name.startswith('__'):
                package_import = f'{root.name}.{package_path.name}'

                with Cluster(package_import, direction='TB'):

                    for module_path in sorted(package_path.iterdir()):
                        if not module_path.name.startswith('__'):
                            module_import = f'{package_import}.{module_path.stem}'
                            module = import_module(module_import)

                            classes = []
                            for name in dir(module):
                                if not name.startswith('_'):
                                    class_ = getattr(module, name)
                                    if class_ not in classes:
                                        classes.append(class_)

                            if not classes:
                                continue

                            with Cluster(module_import, direction='TB'):
                                prev_node = None
                                for class_ in reversed(classes):
                                    node = class_(class_.__name__)
                                    if prev_node is not None:
                                        node - Edge(style='invis') - prev_node
                                    prev_node = node

if __name__ == '__main__':
    main()
