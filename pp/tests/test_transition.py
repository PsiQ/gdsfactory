import pytest

import pp
from pp.transition import transition


def test_transition():
    with pytest.raises(ValueError):

        path = pp.Path()
        path.append(pp.path.arc(radius=10, angle=90))
        path.append(pp.path.straight(length=10))
        path.append(pp.path.euler(radius=3, angle=-90))
        path.append(pp.path.straight(length=40))
        path.append(pp.path.arc(radius=8, angle=-45))
        path.append(pp.path.straight(length=10))
        path.append(pp.path.arc(radius=8, angle=45))
        path.append(pp.path.straight(length=10))

        X = pp.CrossSection()
        X.add(width=1, offset=0, layer=0)

        x2 = pp.CrossSection()
        x2.add(width=2, offset=0, layer=0)

        transition(X, x2)


if __name__ == "__main__":
    test_transition()