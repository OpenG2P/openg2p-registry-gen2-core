from abc import ABC, abstractmethod


class G2PScoreComputeInterface(ABC):
    """
    Domain-specific score compute contract.
    Implementations live in `openg2p_registry_extensions.score_compute.services`.
    """

    @abstractmethod
    async def compute_score(
        self,
        link_internal_record_id: str,
        contributing_attribute_values: dict,
        score_config: dict,
    ) -> float:
        """
        Compute and return the score for the given record.

        Args:
            link_internal_record_id: Registrant / domain record internal ID.
            contributing_attribute_values: Snapshot keyed by attribute_name (from the queue).
            score_config: Assembled from `g2p_register_score_contributing_attributes`, including
                ``contributing_attributes`` (list of definition rows) and a ``weights`` map
                ``{attribute_name: attribute_weightage}`` for backward compatibility.
        """
