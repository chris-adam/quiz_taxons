from . import views
from django.urls import path


urlpatterns = [
    path("", views.index, name="index"),
    path("images_grid/<int:taxon_id>/", views.render_images_grid, name="images_grid"),
    path("submit_answer/", views.render_result, name="submit_answer"),
    path("show_propositions/", views.show_propositions, name="show_propositions"),
    path("skip_question/", views.skip_question, name="skip_question"),
]
