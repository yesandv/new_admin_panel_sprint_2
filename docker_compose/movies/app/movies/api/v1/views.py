from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q, QuerySet, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView

from ...models import FilmWork, Roles


class FilmWorkApiMixin:
    model = FilmWork
    http_method_names = ["get"]

    @staticmethod
    def _annotate(obj: QuerySet) -> QuerySet:
        return obj.annotate(
            genres=Coalesce(
                ArrayAgg("genres__name", distinct=True), Value([])
            ),
            actors=Coalesce(
                ArrayAgg(
                    "persons__full_name",
                    filter=Q(personfilmwork__role=Roles.ACTOR),
                    distinct=True,
                ),
                Value([]),
            ),
            directors=Coalesce(
                ArrayAgg(
                    "persons__full_name",
                    filter=Q(personfilmwork__role=Roles.DIRECTOR),
                    distinct=True,
                ),
                Value([]),
            ),
            writers=Coalesce(
                ArrayAgg(
                    "persons__full_name",
                    filter=Q(personfilmwork__role=Roles.WRITER),
                    distinct=True,
                ),
                Value([]),
            ),
        )

    def get_queryset(self) -> QuerySet:
        film_works = self.model.objects # noqa
        film_work_fields = film_works.values(
            "id", "title", "description", "creation_date", "rating", "type"
        )
        annotated_film_works = self._annotate(film_work_fields)
        return annotated_film_works

    def render_to_response(  # noqa
            self, context: dict, **response_kwargs  # noqa
    ) -> JsonResponse:
        return JsonResponse(context)


class FilmWorkListApi(FilmWorkApiMixin, BaseListView):
    paginate_by = 50

    def get_context_data(
            self, *, object_list: QuerySet = None, **kwargs
    ) -> dict:
        queryset = self.get_queryset()
        paginator, page, queryset, is_paginated = self.paginate_queryset(
            queryset, self.paginate_by
        )
        context = {
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "prev": (
                page.previous_page_number() if page.has_previous() else None
            ),
            "next": page.next_page_number() if page.has_next() else None,
            "results": list(queryset),
        }
        return context


class FilmWorkDetailApi(FilmWorkApiMixin, BaseDetailView):

    def get_context_data(self, **kwargs) -> dict:
        return kwargs["object"]
