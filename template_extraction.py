#!/usr/bin/env python3
import itertools
import os
import spacy

nlp = spacy.load('en')
PATH = "./full_text/"


def turn_titles_into_sentences(raw_text):
    """
    Spacy is not quite clever enough to separate the title of an article from the
    first sentence. This seems to cause problems with the POS-tagging. This function
    adds full stops at the end of title lines.
    """
    paragraphs = raw_text.split("\n")
    i = 0
    while i < len(paragraphs) and not paragraphs[i].endswith("."):
        if paragraphs[i]:
            paragraphs[i] = paragraphs[i].strip() + "."
        i += 1

    text = "\n".join(paragraphs)
    return(text)


def get_spacy_text(raw_text):
    """Process text with spaCy."""
    detitled = turn_titles_into_sentences(raw_text)
    try:
        u_text = detitled.decode("utf-8")
    except(UnicodeEncodeError, AttributeError):
        u_text = detitled
    text = nlp(u_text)
    return(text)


class Relationship(object):

    def __init__(self, token1, token2):
        self.token1 = token1
        self.token2 = token2
        common_ancestors, branch1, branch2 = self.find_relationship()
        self.common_ancestors = common_ancestors
        self.branch1 = branch1
        self.branch2 = branch2

    def __str__(self):
        return("{}\u2013{}".format(self.token1, self.token2))

    def find_relationship(self):
        """
        Walks up the syntactic tree from two tokens in the same sentence to the root.
        This should return a structure with a stem and two branches;
        the stem being the common ancestors of the two tokens.
        """
        chain1 = [self.token1] + list(self.token1.ancestors)
        chain2 = [self.token2] + list(self.token2.ancestors)

        # find the first common ancestor
        for i, token in enumerate(chain1):
            if token in chain2:
                i1 = i
                break

        try:
            i2 = chain2.index(chain1[i1])
        except NameError:
            raise ValueError("""The two tokens, {} and {} are unrelated! Are you sure they
                             are from the same sentence?""".format(self.token1, self.token2))

        # the two branches
        branch1 = chain1[:i1][::-1]
        branch2 = chain2[:i2][::-1]

        if chain1[i1:] != chain2[i2:]:
            raise ValueError("""There is ambiguity about the chain before it forks:
                             {} != {}.""".format(chain1[i1:], chain2[i2:]))
        else:
            return(chain1[i1:][::-1], branch1, branch2)

    @property
    def longer_branch(self):
        if len(self.branch1) >= len(self.branch2):
            return(self.branch1)
        else:
            return(self.branch2)

    @property
    def shorter_branch(self):
        if len(self.branch2) <= len(self.branch1):
            return(self.branch2)
        else:
            return(self.branch1)

    @property
    def forking_node(self):
        return(self.common_ancestors[-1])

    def display(self):
        print(u"                   DEP   POS")
        print(u"ANCESTORS:         ---   ---")
        for i, token in enumerate(self.common_ancestors):
            if i == len(self.common_ancestors) - 1:
                print("{:>13}{:>9}{:>6} (fork)".format(token.orth_, token.dep_, token.pos_))
            else:
                print("{:>13}{:>9}{:>6}".format(token.orth_, token.dep_, token.pos_))

        print(u"            \u2502")
        print(u"FORKS:      \u251c" + "".join([u"\u2500"] * 38) + "\u2510")
        for i, token1 in enumerate(self.longer_branch):
            try:
                token2 = self.shorter_branch[i]
                if i == len(self.longer_branch) - 1 and i == len(self.shorter_branch) - 1:
                    print("{:>13}{:>9}{:>6} (token 1) {:>13}{:>9}{:>6} (token 2)".format(
                        token1.orth_, token1.dep_, token1.pos_, token2.orth_, token2.dep_, token2.pos_))
                elif i == len(self.shorter_branch) - 1:
                    print("{:>13}{:>9}{:>6}           {:>13}{:>9}{:>6} (token 2)".format(
                        token1.orth_, token1.dep_, token1.pos_, token2.orth_, token2.dep_, token2.pos_))
                else:
                    print("{:>13}{:>9}{:>6}           {:>13}{:>9}{:>6}".format(
                        token1.orth_, token1.dep_, token1.pos_, token2.orth_, token2.dep_, token2.pos_))
            except IndexError:
                if i == len(self.longer_branch) - 1:
                    print("{:>13}{:>9}{:>6} (token 1)".format(token1.orth_, token1.dep_, token1.pos_))
                else:
                    print("{:>13}{:>9}{:>6}".format(token1.orth_, token1.dep_, token1.pos_))


def main(entity1, entity2):
    print("Entities:")
    print(" -" + ", ".join("{}: {}".format(k, v) for k, v in entity1.items()))
    print(" -" + ", ".join("{}: {}".format(k, v) for k, v in entity2.items()))

    # Do these entities contain any names that could be used to filter
    # the datafiles?
    names = [entity["lower"] for entity in (entity1, entity2) if "lower" in entity]
    # This bash command returns all the files where the two entities
    # occur in the same line, e.g.:
    # find ./full_text -type f -print0 | xargs -0 grep -l -E "London.*Manchester|Manchester.*London"
    if len(names) == 2:
        cmd = 'find {} -type f -print0 | xargs -0 grep -l -i -E "{}.*{}|{}.*{}"'.format(
            PATH, names[0], names[1], names[1], names[0])
    elif len(names) == 1:
        cmd = 'find {} -type f -print0 | xargs -0 grep -l -i -E "{}"'.format(
            PATH, names[0])
    else:
        cmd = 'find {} -type f'.format(PATH)

    # run the command and save the output
    os.system(cmd + " > stdout.txt")
    with open("stdout.txt") as f:
        stdout = f.read()

    filenames = [filename for filename in stdout.split("\n") if filename]

    print("")
    print("Files found: {}.".format(len(filenames)))

    # search through each file found and get relationships between the entities
    relationships = []
    for filename in filenames:
        print(filename)
        with open(filename, "r") as f:
            text = f.read()

        doc = get_spacy_text(text)  # process with spacy
        for entity in doc.ents:
            entity.merge()  # merge any entities extracted into a single token
        # for chunk in doc.noun_chunks:
        #     chunk.merge()

        for sentence in doc.sents:  # search for pairs within each sentence
            entity1_instances = []
            entity2_instances = []
            for token in sentence:
                if all(v.lower() in getattr(token, k + "_").lower() for k, v in entity1.items()):
                    entity1_instances.append(token)
                if all(v.lower() in getattr(token, k + "_").lower() for k, v in entity2.items()):
                    entity2_instances.append(token)

            entity_pairs = itertools.product(entity1_instances, entity2_instances)
            relationships += [(Relationship(pair[0], pair[1]), sentence) for pair in entity_pairs]

    print("Relationships found: {}.".format(len(relationships)))

    for thing in relationships:
        # each thing is a tuple of (Relationship, sentence)
        print("")
        print("".join(["-"] * 77))
        print(thing[1])
        print("".join(["-"] * 77))
        thing[0].display()

if __name__ == '__main__':
    main({"lower": "Balderton"}, {"lower": "company"})
