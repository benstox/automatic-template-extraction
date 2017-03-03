#!/usr/bin/env python3


def match_node_pattern_(node, pattern):
    """
    Testing.
    """
    return(all(node[key] == value for key, value in pattern.items()))


def follow_branch_(node, branch):
    """
    Testing.
    """
    count = 0
    if branch:
        matches = [child for child in node["children"] if match_node_pattern_(child, branch[0])]
        if not matches:
            return(0)

        count += sum(follow_branch_(match, branch[1:]) for match in matches)
        return(count)
    else:
        return(1)


branch = [{"value": "A"}, {"value": "B"}, {"value": "C"}]

tree = {
    "value": "START",
    "children": [
        {
            "value": "A",
            "children": []
        },
        {
            "value": "B",
            "children": [
                {
                    "value": "D",
                    "children": []
                },
            ]
        },
        {
            "value": "A",
            "children": [
                {
                    "value": "B",
                    "children": [
                        {
                            "value": "C",
                            "children": []
                        },
                        {
                            "value": "C",
                            "children": []
                        },
                    ]
                },
                {
                    "value": "D",
                    "children": []
                },
            ]
        },
    ]
}

assert follow_branch_(tree, branch) == 2
