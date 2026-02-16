from neomodel import (
    StructuredNode,
    StringProperty,
    IntegerProperty,
    UniqueIdProperty,
    RelationshipTo,
    RelationshipFrom
)


class Team(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True, unique_index=True)

    members = RelationshipFrom('Member', 'MEMBER_OF')

    def __str__(self):
        return f"Team: {self.name}"


class Member(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    age = IntegerProperty(default=67)

    team = RelationshipTo(Team, 'MEMBER_OF')

    def __str__(self):
        return f"{self.name} ({self.age})"
