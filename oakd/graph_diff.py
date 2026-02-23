"""
Graph Diffing and Versioning Module

Provides:
- Graph diffing between versions (version A vs version B)
- Schema migration support
- Backward compatibility verification
- Change detection and reporting
"""

import json
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ChangeType(Enum):
    """Types of changes in graph diff"""
    NODE_ADDED = "node_added"
    NODE_REMOVED = "node_removed"
    NODE_MODIFIED = "node_modified"
    EDGE_ADDED = "edge_added"
    EDGE_REMOVED = "edge_removed"
    EDGE_MODIFIED = "edge_modified"
    ATTRIBUTE_CHANGED = "attribute_changed"


@dataclass
class GraphChange:
    """Represents a single change in graph diff"""
    change_type: ChangeType
    element_id: str  # Node ID or edge ID
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    attribute_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'change_type': self.change_type.value,
            'element_id': self.element_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'attribute_name': self.attribute_name,
            'metadata': self.metadata
        }


@dataclass
class GraphDiff:
    """Complete diff between two graph versions"""
    version_a: str
    version_b: str
    changes: List[GraphChange]
    added_nodes: int = 0
    removed_nodes: int = 0
    modified_nodes: int = 0
    added_edges: int = 0
    removed_edges: int = 0
    modified_edges: int = 0
    compatible: bool = True
    compatibility_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'version_a': self.version_a,
            'version_b': self.version_b,
            'changes': [c.to_dict() for c in self.changes],
            'added_nodes': self.added_nodes,
            'removed_nodes': self.removed_nodes,
            'modified_nodes': self.modified_nodes,
            'added_edges': self.added_edges,
            'removed_edges': self.removed_edges,
            'modified_edges': self.modified_edges,
            'compatible': self.compatible,
            'compatibility_issues': self.compatibility_issues
        }

    def get_summary(self) -> str:
        """Get human-readable summary"""
        return (
            f"Graph Diff {self.version_a} → {self.version_b}:\n"
            f"  Nodes: +{self.added_nodes} -{self.removed_nodes} ~{self.modified_nodes}\n"
            f"  Edges: +{self.added_edges} -{self.removed_edges} ~{self.modified_edges}\n"
            f"  Compatible: {self.compatible}\n"
            f"  Total Changes: {len(self.changes)}"
        )


class GraphDiffer:
    """
    Computes diffs between graph versions.

    Supports:
    - Structural diffs
    - Attribute diffs
    - Compatibility checking
    """

    def diff_graphs(
        self,
        graph_a,
        graph_b,
        version_a: str = "unknown",
        version_b: str = "unknown"
    ) -> GraphDiff:
        """
        Compute diff between two graphs.

        Args:
            graph_a: First graph (NetworkX)
            graph_b: Second graph (NetworkX)
            version_a: Version identifier for graph A
            version_b: Version identifier for graph B

        Returns:
            GraphDiff object with all changes
        """
        changes = []

        # Get node sets
        nodes_a = set(graph_a.nodes())
        nodes_b = set(graph_b.nodes())

        # Find added/removed nodes
        added_nodes = nodes_b - nodes_a
        removed_nodes = nodes_a - nodes_b
        common_nodes = nodes_a & nodes_b

        for node in added_nodes:
            changes.append(GraphChange(
                change_type=ChangeType.NODE_ADDED,
                element_id=node,
                new_value=dict(graph_b.nodes[node])
            ))

        for node in removed_nodes:
            changes.append(GraphChange(
                change_type=ChangeType.NODE_REMOVED,
                element_id=node,
                old_value=dict(graph_a.nodes[node])
            ))

        # Check for modified nodes
        for node in common_nodes:
            attrs_a = dict(graph_a.nodes[node])
            attrs_b = dict(graph_b.nodes[node])

            if attrs_a != attrs_b:
                node_changes = self._diff_attributes(node, attrs_a, attrs_b)
                changes.extend(node_changes)

        # Get edge sets
        edges_a = set(graph_a.edges())
        edges_b = set(graph_b.edges())

        added_edges = edges_b - edges_a
        removed_edges = edges_a - edges_b
        common_edges = edges_a & edges_b

        for edge in added_edges:
            edge_id = f"{edge[0]}->{edge[1]}"
            changes.append(GraphChange(
                change_type=ChangeType.EDGE_ADDED,
                element_id=edge_id,
                new_value=dict(graph_b.edges[edge])
            ))

        for edge in removed_edges:
            edge_id = f"{edge[0]}->{edge[1]}"
            changes.append(GraphChange(
                change_type=ChangeType.EDGE_REMOVED,
                element_id=edge_id,
                old_value=dict(graph_a.edges[edge])
            ))

        # Check for modified edges
        for edge in common_edges:
            attrs_a = dict(graph_a.edges[edge])
            attrs_b = dict(graph_b.edges[edge])

            if attrs_a != attrs_b:
                edge_id = f"{edge[0]}->{edge[1]}"
                edge_changes = self._diff_attributes(edge_id, attrs_a, attrs_b)
                changes.extend(edge_changes)

        # Create diff
        diff = GraphDiff(
            version_a=version_a,
            version_b=version_b,
            changes=changes,
            added_nodes=len(added_nodes),
            removed_nodes=len(removed_nodes),
            modified_nodes=sum(1 for c in changes if c.change_type == ChangeType.NODE_MODIFIED),
            added_edges=len(added_edges),
            removed_edges=len(removed_edges),
            modified_edges=sum(1 for c in changes if c.change_type == ChangeType.EDGE_MODIFIED)
        )

        # Check compatibility
        diff.compatible, diff.compatibility_issues = self._check_compatibility(diff)

        return diff

    def _diff_attributes(
        self,
        element_id: str,
        attrs_a: Dict,
        attrs_b: Dict
    ) -> List[GraphChange]:
        """Diff attributes between two versions"""
        changes = []

        all_keys = set(attrs_a.keys()) | set(attrs_b.keys())

        for key in all_keys:
            val_a = attrs_a.get(key)
            val_b = attrs_b.get(key)

            if val_a != val_b:
                changes.append(GraphChange(
                    change_type=ChangeType.ATTRIBUTE_CHANGED,
                    element_id=element_id,
                    attribute_name=key,
                    old_value=val_a,
                    new_value=val_b
                ))

        return changes

    def _check_compatibility(self, diff: GraphDiff) -> Tuple[bool, List[str]]:
        """
        Check if graphs are backward compatible.

        Compatibility rules:
        - Removed nodes break compatibility (data loss)
        - Removed edges break compatibility (relationship loss)
        - Modified critical attributes break compatibility
        - Added nodes/edges maintain compatibility
        """
        issues = []

        if diff.removed_nodes > 0:
            issues.append(f"Removed {diff.removed_nodes} nodes (data loss)")

        if diff.removed_edges > 0:
            issues.append(f"Removed {diff.removed_edges} edges (relationship loss)")

        # Check for critical attribute changes
        critical_attrs = {'node_type', 'edge_type', 'claim_type', 'confidence'}
        for change in diff.changes:
            if change.change_type == ChangeType.ATTRIBUTE_CHANGED:
                if change.attribute_name in critical_attrs:
                    issues.append(
                        f"Critical attribute '{change.attribute_name}' changed "
                        f"for {change.element_id}"
                    )

        compatible = len(issues) == 0
        return compatible, issues


class SchemaMigrator:
    """
    Handles schema migration between versions.

    Ensures backward compatibility and data preservation.
    """

    def __init__(self):
        self._migrations: Dict[Tuple[str, str], Any] = {}

    def register_migration(
        self,
        from_version: str,
        to_version: str,
        migration_func: Any
    ):
        """Register migration function"""
        self._migrations[(from_version, to_version)] = migration_func

    def migrate_graph(
        self,
        graph,
        from_version: str,
        to_version: str
    ):
        """
        Migrate graph from one schema version to another.

        Args:
            graph: Graph to migrate
            from_version: Source schema version
            to_version: Target schema version

        Returns:
            Migrated graph

        Raises:
            ValueError: If migration path not found
        """
        if (from_version, to_version) not in self._migrations:
            raise ValueError(
                f"No migration found from {from_version} to {to_version}"
            )

        migration_func = self._migrations[(from_version, to_version)]
        return migration_func(graph)

    def get_migration_path(
        self,
        from_version: str,
        to_version: str
    ) -> Optional[List[str]]:
        """
        Find migration path between versions.

        Returns list of versions to migrate through, or None if no path exists.
        """
        # Simplified - assumes direct migration exists
        if (from_version, to_version) in self._migrations:
            return [from_version, to_version]

        return None


class VersionCompatibilityChecker:
    """
    Checks version compatibility between system components.
    """

    def __init__(self):
        self._compatible_versions: Dict[str, Set[str]] = {}

    def register_compatibility(
        self,
        version: str,
        compatible_with: Set[str]
    ):
        """Register compatible versions"""
        self._compatible_versions[version] = compatible_with

    def is_compatible(
        self,
        version_a: str,
        version_b: str
    ) -> bool:
        """Check if two versions are compatible"""
        if version_a == version_b:
            return True

        if version_a in self._compatible_versions:
            return version_b in self._compatible_versions[version_a]

        if version_b in self._compatible_versions:
            return version_a in self._compatible_versions[version_b]

        return False

    def get_compatible_versions(self, version: str) -> Set[str]:
        """Get all compatible versions for a version"""
        return self._compatible_versions.get(version, set())
