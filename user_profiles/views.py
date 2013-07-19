import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils import simplejson

from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic.edit import UpdateView

from misc.views import set_style
from user_profiles.filters import ProfileFilter
from user_profiles.forms import PublicProfileForm, ProfileSettingsForm


UserModel = get_user_model()
past_year = datetime.datetime.now() - datetime.timedelta(days=365)


class MemberList(ListView):
    """
    Renders either default user list (paginated) or search results.
    To-do: split search to separate view, make pagination work better.
    """
    queryset = UserModel.objects.filter(preferred_name__gt="", is_active=1, last_login__gte=past_year, post_count__gte=1).order_by('preferred_name').values()
    template_name = "users/user_list.html"
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super(MemberList, self).get_context_data(**kwargs)
        if 'preferred_name' in self.request.GET:
            filter = ProfileFilter(self.request.GET, queryset=self.queryset)
        else:
            filter = ProfileFilter()
        context['filter'] = filter
        return context


class EditProfile(UpdateView):
    model = UserModel
    template_name = "users/user_edit_form.html"
    form_class = PublicProfileForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(EditProfile, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super(EditProfile, self).get_context_data(**kwargs)
        context['settings_form'] = ProfileSettingsForm(instance=self.get_object())
        return context


class EditProfileSettings(EditProfile):
    form_class = ProfileSettingsForm

    def get_context_data(self, **kwargs):
        context = super(EditProfileSettings, self).get_context_data(**kwargs)
        context['settings_form'] = self.form_class
        context['form'] = PublicProfileForm()
        return context

    def form_valid(self, form, *args, **kwargs):
        messages.success(self.request, "Your settings have been updated.")
        theme = form.cleaned_data.get('theme')
        if theme:
            self.request.COOKIES['theme'] = theme
        return super(EditProfile, self).form_valid(form, *args, **kwargs)


def view_profile(request, slug='', pk=''):
    """ Returns detail view for a single user """
    if pk:
        user = get_object_or_404(UserModel, id=pk)
    else:
        user = get_object_or_404(UserModel, username=slug)

    if request.is_ajax():
        location = user.city
        if user.state:
            location += ", %s" % user.state
        xhr_dict = {
            'name': user.preferred_name,
            'posts': user.post_count,
            'username': user.username,
            'joined': user.date_joined.strftime('%m/%d/%Y'),
            'location': location or '',
            'website': user.homepage or '',
            'profile_url': user.get_absolute_url(),
            'contact_url': reverse('contact_member', args=(user.username,)),
        }
        return HttpResponse(simplejson.dumps(xhr_dict), mimetype='application/javascript')
    return render(request, "users/user_detail.html", {'user': user})
