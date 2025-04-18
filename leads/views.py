import datetime
from django.core.mail import send_mail
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views import generic
from .models import Lead, Agent, Category
from .forms import  LeadModelForm, LeadForm, CustomUserCreationForm,AssignAgentForm,LeadCategoryUpdateForm,CategoryModelForm
from agents.mixins import OrganisorAndLoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Count
from django.db.models.functions import TruncDate
#from chatbot.emotion_model.emotion_predict import predict_emotion



# CRUD+L - Create, Retrieve, Update and Delete + List

class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

    def get_success_url(self):
        return reverse("login")


class LandingPageView(generic.TemplateView):
    template_name = "landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class DashboardView(OrganisorAndLoginRequiredMixin, generic.TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        thirty_days_ago = datetime.date.today() - datetime.timedelta(days=30)

        # Stats
        total_lead_count = Lead.objects.filter(organisation=user.userprofile).count()
        total_in_past30 = Lead.objects.filter(
            organisation=user.userprofile,
            date_added__gte=thirty_days_ago
        ).count()

        completed_category, _ = Category.objects.get_or_create(name="Completed", organisation=user.userprofile)
        completed_in_past30 = Lead.objects.filter(
            organisation=user.userprofile,
            category=completed_category,
            completed_date__gte=thirty_days_ago
        ).count()

        # Leads per date for the line chart
        leads_by_day_qs = (
            Lead.objects.filter(organisation=user.userprofile, date_added__gte=thirty_days_ago)
            .annotate(day=TruncDate('date_added'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        leads_by_date = list(leads_by_day_qs)

        # Leads per category (optional)
        categories = Category.objects.filter(organisation=user.userprofile)
        category_data = [
            {
                "name": category.name,
                "count": Lead.objects.filter(organisation=user.userprofile, category=category).count()
            }
            for category in categories
        ]

        context.update({
            "total_lead_count": total_lead_count,
            "total_in_past30": total_in_past30,
            "completed_in_past30": completed_in_past30,
            "category_data": category_data,
            "leads_by_date": json.dumps(leads_by_date, default=str),  # 👈 convert to JSON + date string
        })
        return context

def landing_page(request):
    return render(request, "landing.html")

class LeadListView(LoginRequiredMixin,generic.ListView):
      template_name = "leads/lead_list.html"
      context_object_name ="leads"

      def get_queryset(self):
        user = self.request.user

        if user.is_organisor:
           queryset = Lead.objects.filter(
               organisation=user.userprofile, 
                agent__isnull=False
                )
        else:
            queryset = Lead.objects.filter(
                organisation=user.agent.organisation, 
                agent__isnull=False
                )
            
            queryset = queryset.filter(agent__user=user)
        return queryset
      
      def get_context_data(self, **kwargs):
        context = super(LeadListView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.filter(
                organisation=user.userprofile, 
                agent__isnull=True
            )
            context.update({
                "unassigned_leads": queryset
            })
        return context

def lead_list(request):
    leads= Lead.objects.all()
    context = {
        "leads":leads
    }
    return render(request,"leads/lead_list.html",context)

class LeadDetailView(LoginRequiredMixin,generic.DetailView):
      template_name = "leads/lead_detail.html"
      context_object_name ="lead"

      def get_queryset(self):
        user = self.request.user

        if user.is_organisor:
           queryset = Lead.objects.filter(organisation=user.userprofile,)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation,)
            
            queryset = queryset.filter(agent__user=user)
        return queryset

def lead_detail(request,pk):
    print(pk)
    lead= Lead.objects.get(id=pk)
    context ={
        "lead":lead
    }
    return render(request,"leads/lead_detail.html",context)

class LeadCreateView(OrganisorAndLoginRequiredMixin,generic.CreateView):
      template_name = "leads/lead_create.html"
      form_class=LeadModelForm

      def get_success_url(self):
        return reverse ("leads:lead-list")
      
      def form_valid(self, form):
        lead = form.save(commit=False)
        lead.organisation = self.request.user.userprofile
        lead.save()
        send_mail(
            subject="A lead has been created",
            message="Go to the site to see the new lead",
            from_email="test@test.com",
            recipient_list=["test2@test.com"]
        )
        return super (LeadCreateView,self).form_valid(form)

def lead_create(request):
    form=LeadModelForm()
    if request.method == "POST":
        form=LeadModelForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect("/leads")
    context ={
        "form":form
    }
    return render(request, "leads/lead_create.html",context)


class LeadUpdateView(OrganisorAndLoginRequiredMixin,generic.UpdateView):
      template_name = "leads/lead_update.html"
      form_class=LeadModelForm

      def get_queryset(self):
        user = self.request.user    
        return Lead.objects.filter(organisation=user.userprofile,)

      def get_success_url(self):
        return reverse ("leads:lead-list")


def lead_update(request, pk):
    lead = Lead.objects.get(id=pk)
    form=LeadModelForm(instance=lead)
    if request.method == "POST":
        form=LeadModelForm(request.POST,instance=lead)
        if form.is_valid():
            form.save()
        return redirect("/leads")
    context = {
        "form":form,
        "lead" : lead 
    }
    return render(request, "leads/lead_update.html",context)

class LeadDeleteView(OrganisorAndLoginRequiredMixin,generic.DeleteView):
    template_name = "leads/lead_delete.html"

    def get_success_url(self):
        return reverse ("leads:lead-list")
      
    def get_queryset(self):
        user = self.request.user    
        return Lead.objects.filter(organisation=user.userprofile,)

def lead_delete(request, pk):
    lead = Lead.objects.get(id=pk)
    lead.delete()
    return redirect("/leads")


class AssignAgentView(OrganisorAndLoginRequiredMixin, generic.FormView):
    template_name = "leads/assign_agent.html"
    form_class = AssignAgentForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(AssignAgentView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request": self.request
        })
        return kwargs

    def get_success_url(self):
        return reverse ("leads:lead-list")
    
    def form_valid(self, form):
        agent = form.cleaned_data["agent"]
        lead = Lead.objects.get(id=self.kwargs["pk"])
        lead.agent = agent
        lead.save()
        return super(AssignAgentView, self).form_valid(form)
    

class CategoryListView(LoginRequiredMixin, generic.ListView):
    template_name = "leads/category_list.html"
    context_object_name = "category_list"

    def get_context_data(self, **kwargs):
        context = super(CategoryListView, self).get_context_data(**kwargs)
        user = self.request.user

        if user.is_organisor:
            leads = Lead.objects.filter(organisation=user.userprofile)
        else:
            leads = Lead.objects.filter(organisation=user.agent.organisation)

        # Get unassigned lead count
        unassigned_lead_count = leads.filter(category__isnull=True).count()

        context.update({
            "unassigned_lead_count": unassigned_lead_count
        })
        return context

    def get_queryset(self):
        user = self.request.user

        if user.is_organisor:
            queryset = Category.objects.filter(
                organisation=user.userprofile
            ).annotate(lead_count=Count("leads"))
        else:
            queryset = Category.objects.filter(
                organisation=user.agent.organisation
            ).annotate(lead_count=Count("leads"))

        return queryset

class CategoryDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "leads/category_detail.html"
    context_object_name = "category"

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Category.objects.filter(
                organisation=user.userprofile
            )
        else:
            queryset = Category.objects.filter(
                organisation=user.agent.organisation
            )
        return queryset
    
class CategoryCreateView(OrganisorAndLoginRequiredMixin, generic.CreateView):
    template_name = "leads/category_create.html"
    form_class = CategoryModelForm

    def get_success_url(self):
        return reverse("leads:category-list")

    def form_valid(self, form):
        category = form.save(commit=False)
        category.organisation = self.request.user.userprofile
        category.save()
        return super(CategoryCreateView, self).form_valid(form)

class CategoryUpdateView(OrganisorAndLoginRequiredMixin, generic.UpdateView):
    template_name = "leads/category_update.html"
    form_class = CategoryModelForm

    def get_success_url(self):
        return reverse("leads:category-list")

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Category.objects.filter(
                organisation=user.userprofile
            )
        else:
            queryset = Category.objects.filter(
                organisation=user.agent.organisation
            )
        return queryset 

class CategoryDeleteView(OrganisorAndLoginRequiredMixin, generic.DeleteView):
    template_name = "leads/category_delete.html"

    def get_success_url(self):
        return reverse("leads:category-list")

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Category.objects.filter(
                organisation=user.userprofile
            )
        else:
            queryset = Category.objects.filter(
                organisation=user.agent.organisation
            )
        return queryset

class LeadCategoryUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "leads/lead_category_update.html"
    form_class = LeadCategoryUpdateForm

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)
            # filter for the agent that is logged in
            queryset = queryset.filter(agent__user=user)
        return queryset
    
    def form_valid(self, form):
        lead = form.save(commit=False)
        lead.category = form.cleaned_data["category"]  # Ensure the category is updated
        lead.save()
        print(f"Lead {lead.id} assigned to category: {lead.category}")  # Debugging
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("leads:lead-detail", kwargs={"pk": self.get_object().id})


@csrf_exempt
def chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message')

        # Add your AI logic here (e.g., call an AI API or use a chatbot library)
        ai_response = f"AI: You said '{user_message}'"

        return JsonResponse({'response': ai_response})
    return JsonResponse({'error': 'Invalid request'}, status=400)




