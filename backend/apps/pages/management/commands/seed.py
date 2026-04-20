from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from neomodel import StructuredNode, db

from apps.pages import models as page_models

from apps.users.models import User

# Const for path to json
# Change if you need
FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "fixtures"
    / "lotr_data.json"
)

# Mapping type of nodes
NODE_MODELS: dict[str, type[StructuredNode]] = {
    "character": page_models.Character,
    "race": page_models.Race,
    "location": page_models.Location,
    "event": page_models.Event,
    "organization": page_models.Organization,
    "timeline": page_models.Timeline,
    "item": page_models.Item,
    "language": page_models.Language,
    "script": page_models.Script,
    "category": page_models.Category,
    "article": page_models.Article,
}

# Mapping tipe of relation
REL_ATTRIBUTES: dict[str, str | None] = {
    "CHILD_OF": "child_of",
    "MARRIED_TO": "married_to",
    "SIBLING_OF": "sibling_of",
    "OF_RACE": "race",
    "BORN_IN": "born_in",
    "DIED_IN": "died_in",
    "DWELLED_IN": "dwelled_in",
    "SPEAKS": "speaks",
    "MEMBER_OF": "member_of",
    "PARTICIPATED_IN": "participated_in",
    "LIVED_DURING": "lived_during",
    "RULED": None,
    "WIELDS": "wields",
    "OWNS": "owns",
    "BORE": "bore",
    "CRAFTED": "crafted",
    "SUBRACE_OF": "subrace_of",
    "INHABITS": "inhabits",
    "REGION_OF": "region_of",
    "TOOK_PLACE_IN": "took_place_in",
    "PART_OF": "part_of",
    "OCCURRED_DURING": "occurred_during",
    "BASED_IN": "based_in",
    "IS_SPOKEN_BY": "spoken_by",
    "SPOKEN_IN": "spoken_in",
    "WRITTEN_IN": "written_in",
    "HAS_ARTICLE": "article",
    "IN_CATEGORY": "categories",
    "SUBCATEGORY_OF": "subcategories",
}


class Command(BaseCommand):
    help = "Idempotently seed Neo4j and SQLite with mock data"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--force",
            action="store_true",
            help="Update existing nodes and edges (otherwise skip)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        force: bool = options["force"]

        if not FIXTURE_PATH.exists():
            self.stderr.write(f"Json not found: {FIXTURE_PATH}")
            return

        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        self.stdout.write("Seeding database...")

        node_map: dict[tuple[str, str], Any] = {}

        category_map = self._create_categories(
            data.get("categories", []), force, node_map
        )

        article_map = self._create_articles(data.get("articles", []), force)

        node_map = self._create_nodes(data, category_map, article_map, force, node_map)

        self._create_edges(data.get("edges", []), node_map, force)

        self._create_users(data.get("users", []))

        self.stdout.write(self.style.SUCCESS("Seeding completed."))

    def _create_categories(
        self, categories_data: list[dict[str, Any]], force: bool, node_map: dict
    ) -> dict[str, page_models.Category]:
        """Create categories, return dict {slug: object}."""
        self.stdout.write("Creating categories...")

        category_map: dict[str, page_models.Category] = {}
        for cat_data in categories_data:
            slug: str = cat_data["slug"]
            name: str = cat_data["name"]
            existing = page_models.Category.nodes.get_or_none(slug=slug)
            if existing and not force:
                self.stdout.write(f"Category {slug} exists, skipping")
                category_map[slug] = existing
                continue
            if existing and force:
                existing.name = name
                existing.save()
                category_map[slug] = existing
                self.stdout.write(f"Updated category {slug}")
            else:
                category = page_models.Category(slug=slug, name=name)
                category.save()
                category_map[slug] = category
                self.stdout.write(f"Created category {slug}")

            node_map[("category", slug)] = category_map[slug]
        return category_map

    def _create_articles(
        self, articles_data: list[dict[str, Any]], force: bool
    ) -> dict[str, page_models.Article]:
        """
        Creates articles and returns a dictionary {key: object}.
        """
        self.stdout.write("Creating articles...")
        article_map: dict[str, page_models.Article] = {}

        for art_data in articles_data:
            key: str = art_data.get("key", art_data.get("text", ""))[:50]
            text: str = art_data["text"]
            image_url: str | None = art_data.get("image_url")

            existing = page_models.Article.nodes.get_or_none(text=text)
            if existing and not force:
                self.stdout.write(f"Article {key} exists, skipping")
                article_map[key] = existing
                continue
            if existing and force:
                existing.text = text
                existing.image_url = image_url
                existing.save()
                article_map[key] = existing
                self.stdout.write(f"Updated article {key}")
            else:
                article = page_models.Article(text=text, image_url=image_url)
                article.save()
                article_map[key] = article
                self.stdout.write(f"Created article {key}")
        return article_map

    def _create_nodes(
        self,
        data: dict[str, Any],
        category_map: dict[str, page_models.Category],
        article_map: dict[str, page_models.Article],
        force: bool,
        node_map: dict[tuple, StructuredNode],
    ) -> dict[tuple, StructuredNode]:
        """Creates nodes of all types, returns dict {(type, slug): node}."""
        self.stdout.write("Creating nodes...")

        for node_type, nodes_data in data.get("nodes", {}).items():
            model_class = NODE_MODELS.get(node_type)
            if not model_class:
                self.stderr.write(f"Unknown node type: {node_type}")
                continue

            for node_data in nodes_data:
                slug: str = node_data["slug"]
                existing = model_class.nodes.get_or_none(slug=slug)
                if existing and not force:
                    self.stdout.write(f"Node {node_type}/{slug} exists, skip")
                    node_map[(node_type, slug)] = existing
                    continue

                base_fields = {
                    "slug": slug, "names": node_data.get("names", [])
                }

                specific_fields = {
                    k: v
                    for k, v in node_data.items()
                    if k not in base_fields
                    and k not in ("categories", "article_key")
                }

                if existing and force:
                    for key, value in base_fields.items():
                        setattr(existing, key, value)
                    for key, value in specific_fields.items():
                        setattr(existing, key, value)
                    existing.save()
                    node = existing
                    self.stdout.write(f"Updated node {node_type}/{slug}")
                else:
                    node = model_class(**base_fields, **specific_fields)
                    node.save()
                    self.stdout.write(f"Created node {node_type}/{slug}")

                node_map[(node_type, slug)] = node

                # Link to article
                article_key = node_data.get("article_key")
                if article_key and article_key in article_map:
                    article = article_map[article_key]
                    if (hasattr(node, "article") and
                            not node.article.is_connected(article)):
                        node.article.connect(article)
                        self.stdout.write(
                            f"Linked article {article_key} to {slug}"
                        )

                # Link to categories
                for cat_slug in node_data.get("categories", []):
                    category = category_map.get(cat_slug)
                    if category and not node.categories.is_connected(category):
                        node.categories.connect(category)
                        self.stdout.write(f"Link category {cat_slug} to {slug}")

        return node_map

    def _create_edges(
        self,
        edges_data: list[dict[str, Any]],
        node_map: dict[tuple, StructuredNode],
        force: bool,
    ) -> None:
        """Creates edges between nodes using Cypher."""

        self.stdout.write("Creating edges...")
        for edge in edges_data:
            from_type: str = edge["from_type"]
            from_slug: str = edge["from_slug"]
            to_type: str = edge["to_type"]
            to_slug: str = edge["to_slug"]
            rel_type: str = edge["rel_type"]
            properties: dict[str, Any] = {
               k: v for k, v in edge.get("properties", {}).items() if v is not None
            }

            from_node = node_map.get((from_type, from_slug))
            to_node = node_map.get((to_type, to_slug))
            if not from_node or not to_node:
                self.stderr.write(
                    f"Missing nodes for edge {rel_type}: "
                    f"{from_type}/{from_slug} -> {to_type}/{to_slug}"
                )
                continue

            from_id = from_node.element_id
            to_id = to_node.element_id

            if properties:
                props_str = ", ".join(f"{k}: ${k}" for k in properties.keys())
                query = f"""
                    MATCH (a) WHERE elementId(a) = $from_id
                    MATCH (b) WHERE elementId(b) = $to_id
                    MERGE (a)-[r:`{rel_type}` {{{props_str}}}]->(b)
                    RETURN r
                """
            else:
                query = f"""
                    MATCH (a) WHERE elementId(a) = $from_id
                    MATCH (b) WHERE elementId(b) = $to_id
                    MERGE (a)-[r:`{rel_type}`]->(b)
                    RETURN r
                """

            params = {"from_id": from_id, "to_id": to_id}
            params.update(properties)

            try:
                db.cypher_query(query, params)
                self.stdout.write(f"Created/merged edge {rel_type}: "
                                  f"from {from_slug} to {to_slug}")
            except Exception as e:
                self.stderr.write(f"Failed to create edge {rel_type}: {e}")

    def _create_users(self, users_data: list[dict[str, Any]]) -> None:
        """Creates debug users in Django and UserRef in Neo4j."""
        self.stdout.write("Creating debug users...")
        for user_data in users_data:
            username: str = user_data["username"]
            password: str = user_data["password"]
            role: str = user_data.get("role", "viewer")

            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)
                user.role = role
                user.save()
                self.stdout.write(
                    f"Created Django user {username} with role {role}"
                )
            else:
                self.stdout.write(f"Django user {username} already exists")

            user_ref = page_models.UserRef.nodes.get_or_none(django_id=user.id)
            if user_ref is None:
                user_ref = page_models.UserRef(django_id=user.id)
                user_ref.save()
                self.stdout.write(f"Created UserRef for {username}")
            else:
                self.stdout.write(f"UserRef for {username} already exists")
