from app.services.search.text_search_service import(
  TextSearchService
)
from app.services.analytics.search_tracking_service import (
    SearchTrackingService
)

from app.models.enums import SearchType
from app.services.search.image_search_service import(
  ImageSearchService
)

class MultimodalSearchService:

    def __init__(self):

        self.text_service = (
            TextSearchService()
        )

        self.image_service = (
            ImageSearchService()
        )

    def search(
        self,
        text_query,
        image_path,
        top_k=10
    ):

        text_results = (
            self.text_service.search(
                text_query,
                top_k=top_k
            )
        )

        image_results = (
            self.image_service.search(
                image_path,
                top_k=top_k
            )
        )

        combined_scores = {}

        for result in text_results:

            product = result["product"]

            score = result["score"]

            combined_scores[
                product.id
            ] = {
                "product": product,
                "score": (
                    0.5 * score
                )
            }

        for result in image_results:

            product = result["product"]

            score = result["score"]

            if product.id in combined_scores:

                combined_scores[
                    product.id
                ]["score"] += (
                    0.5 * score
                )

            else:

                combined_scores[
                    product.id
                ] = {
                    "product": product,
                    "score": (
                        0.5 * score
                    )
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