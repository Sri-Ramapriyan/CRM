from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now



class User(AbstractUser):
    is_organisor = models.BooleanField(default=True)
    is_agent = models.BooleanField(default=False)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

class LeadManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()   

class Lead(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    age = models.IntegerField(default=0)
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    agent = models.ForeignKey("Agent", null=True, blank=True, on_delete=models.SET_NULL)
    category = models.ForeignKey("Category", related_name="leads", null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.CharField(max_length=300, blank=True, null=True)
    profile_picture = models.ImageField(null=True, blank=True, upload_to="profile_pictures/")
    converted_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)



    def save(self, *args, **kwargs):
        if self.category and self.category.name == "Completed" and not self.completed_date:
            self.completed_date = now()  # Set completed_date only if it's not already set
        super().save(*args, **kwargs)

    objects = LeadManager()


    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.email
    
class Category(models.Model):
    name = models.CharField(max_length=30)  
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    

    def __str__(self):
        return self.name
    
    def get_lead_count(self):
        return self.leads.count()

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
    


def post_user_created_signal(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


post_save.connect(post_user_created_signal, sender=User)
    
