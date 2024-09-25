import contextvars

# Global contexts for a diagrams and a cluster.
#
# These global contexts are for letting the clusters and nodes know
# where context they are belong to. So the all clusters and nodes does
# not need to specify the current diagrams or cluster via parameters.
__diagram = contextvars.ContextVar("diagrams")
__cluster = contextvars.ContextVar("cluster")


def getdiagram() -> "Diagram":
    try:
        return __diagram.get()
    except LookupError:
        return None


def setdiagram(diagram: "Diagram"):
    __diagram.set(diagram)


def getcluster() -> "Cluster":
    try:
        return __cluster.get()
    except LookupError:
        return None


def setcluster(cluster: "Cluster"):
    __cluster.set(cluster)