from django.conf import settings
from django.core.paginator import Paginator


def paginator(post_list, request):
    """Пагинатор выводит 10 постов на страницу."""
    paginator = Paginator(post_list, settings.PAGES)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
