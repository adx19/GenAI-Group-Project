from app.services.analytics.search_tracking_service import (
    SearchTrackingService
)

from app.models.enums import SearchType


class MultimodalSearchService:
    """
    Combines text + image search results via score fusion.

    IMPORTANT: Does NOT own TextSearchService or ImageSearchService instances.
    It calls the module-level singletons in app.api.search via getter functions
    to guarantee each model/FAISS index is loaded exactly ONCE across the
    entire process — preventing duplicate ~600 MB CLIP and ~90 MB MiniLM loads.
    """

    def __init__(self):
        pass

    def search(
        self,
        text_query,
        image_path,
        top_k=10
    ):
        # Import getters here (not at module level) to avoid circular imports
        # and to ensure singletons are already initialised before we call them.
        from app.api.search import get_text_service, get_image_service

        text_svc = get_text_service()
        image_svc = get_image_service()

        text_results = text_svc.search(
            text_query,
            top_k=top_k
        )

        image_results = image_svc.search(
            image_path,
            top_k=top_k
        )

        combined_scores = {}

        for result in text_results:
            product = result["product"]
            score = result["score"]
            combined_scores[product.id] = {
                "product": product,
                "score": 0.5 * score,
            }

        for result in image_results:
            product = result["product"]
            score = result["score"]

            if product.id in combined_scores:
                combined_scores[product.id]["score"] += 0.5 * score
            else:
                combined_scores[product.id] = {
                    "product": product,
                    "score": 0.5 * score,
                }

        final_results = sorted(
            combined_scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        tracker = SearchTrackingService()
        tracker.log_search(
            query=text_query,
            search_type=SearchType.MULTIMODAL,
            results_count=len(final_results[:top_k])
        )

        return final_results[:top_k]