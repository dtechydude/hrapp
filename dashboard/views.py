from django.shortcuts import render
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib.auth.models import User
from users.models import Profile
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import  DetailView
import csv
from django.http import HttpResponse
from datetime import date, timedelta
from django.core.mail import send_mass_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# Create your views here.
@login_required
def landing_page(request):
    return render(request, 'dashboard/hrpams_dashboard.html')

@login_required
def dashboard(request):  
    users_num = User.objects.count()
    # employee_num = Employee.objects.count()
    # employee_num_current = Employee.objects.filter(employee_status__in=['active', 'inactive']).count()
    # num_of_category = Category.objects.count()
   
    # inactive_employee = Employee.objects.filter(employee_status='inactive').count()

    # active = Employee.objects.filter(employee_status='active').count()
    

    # try:
    #     num_indept = Employee.objects.filter(department = request.user.employee.department).count()
    # except Employee.DoesNotExist:
    #     num_indept = Employee.objects.filter()
    # # Build a paginator with function based view
    # queryset = Employee.objects.all().order_by("-id")
    # page = request.GET.get('page', 1)
    # paginator = Paginator(queryset, 40)
    # try:
    #     events = paginator.page(page)
    # except PageNotAnInteger:
    #     events = paginator.page(1)
    # except EmptyPage:
    #     events = paginator.page(paginator.num_pages)
    
    
       
    context = {        
        'users_num' :users_num , 
        # 'employee_num_current' : employee_num_current,
        # 'employee_num_current' : employee_num_current
        

    }
        
    return render(request, 'dashboard/portal_home.html', context )    


@login_required        
def help_center(request):
    return render(request, 'dashboard/help_center.html')

@login_required
def support_info(request):
    return render(request, 'dashboard/support_info.html',)

@login_required
def lock_screen(request):
    return render(request, 'dashboard/lockscreen.html')

@login_required
def success_submission(request):
    return render(request, 'dashboard/success_submission.html')


# # email list
# @login_required
# def email_list(request):
#     users = User.objects.all()

    
#     context = {        
#         'users': users,   
#     }
#     return render(request, 'dashboard/email_list.html', context )

# # birthday list
# @login_required
# def birthday_list(request):
#     user_birthday = Profile.objects.all()
#     employee_birthday = Employee.objects.all()
   
#     context = {        
#         'user_birthday': user_birthday,
#         'employee_birthday':employee_birthday,
#     }
#     return render(request, 'dashboard/birthday_list.html', context)



# @login_required
# def payment_instruction(request):
#     return render(request, 'pages/payment_instruction.html')

# @login_required
# def payment_chart(request):
#     return render(request, 'pages/payment_chart.html')




# # students phone list
# @login_required
# def employee_phone_email_view(request):
#     """
#     A view to display a phone list of all employee and allows for CSV export.
#     """
#     students = Student.objects.select_related('user__profile').all().order_by('last_name', 'first_name')

#     if request.GET.get('export') == 'csv':
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="student_phone_list.csv"'

#         writer = csv.writer(response)
#         writer.writerow(['Student Name', 'Student Phone', 'Guardian Name', 'Guardian Phone'])

#         for student in students:
#             writer.writerow([
#                 employee.get_full_name(),
#                 employee.user.profile.phone,
#                 employee.guarantor_name,
#                 employee.guarantor_phone,
#             ])
#         return response

#     context = {
#         'employees': employees,
#     }

#     return render(request, 'pages/students_phone_list.html', context)

# # Students Email List
# @login_required
# def student_email_list_view(request):
#     """
#     A view to display a list of student and guardian emails and allows for CSV export.
#     """
#     students = Student.objects.all().order_by('last_name', 'first_name')

#     if request.GET.get('export') == 'csv':
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="student_email_list.csv"'

#         writer = csv.writer(response)
#         writer.writerow(['Student Name', 'Student Email', 'Guardian Name', 'Guardian Email'])

#         for student in students:
#             writer.writerow([
#                 student.get_full_name(),
#                 student.user.email,
#                 student.guardian_name,
#                 student.guardian_email,
#             ])
#         return response

#     context = {
#         'students': students,
#     }

#     return render(request, 'pages/students_email_list.html', context)

# # Teachers/guarantors Phone List
# @login_required
# def teacher_guarantor_phone_list_view(request):
#     """
#     A view to display a list of teacher guarantor phone numbers and allows for CSV export.
#     """
#     teachers = Teacher.objects.all().order_by('last_name', 'first_name')

#     if request.GET.get('export') == 'csv':
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="teacher_guarantor_phone_list.csv"'

#         writer = csv.writer(response)
#         writer.writerow(['Teacher Name', 'Profile Phone', 'Guarantor Name', 'Guarantor Phone'])

#         for teacher in teachers:
#             writer.writerow([
#                 teacher.get_full_name(),
#                 teacher.phone_home,
#                 teacher.guarantor_name,
#                 teacher.guarantor_phone,
#             ])
#         return response

#     context = {
#         'teachers': teachers,
#     }

#     return render(request, 'pages/teachers_phone_list.html', context)

# # Teachers Email List
# @login_required
# def teacher_guarantor_email_list_view(request):
#     """
#     A view to display a list of teacher guarantor emails and allows for CSV export.
#     """
#     teachers = Teacher.objects.all().order_by('last_name', 'first_name')

#     if request.GET.get('export') == 'csv':
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="teacher_guarantor_email_list.csv"'

#         writer = csv.writer(response)
#         writer.writerow(['Teacher Name', 'Profile Email', 'Guarantor Name', 'Guarantor Email'])

#         for teacher in teachers:
#             writer.writerow([
#                 teacher.get_full_name(),
#                 teacher.user.email,
#                 teacher.guarantor_name,
#                 teacher.guarantor_email,
#             ])
#         return response

#     context = {
#         'teachers': teachers,
#     }

#     return render(request, 'pages/teachers_email_list.html', context)



# @login_required
# def video_guides_view(request):
#     # A placeholder list of video data with an 'is_staff_only' flag
#     video_list = [
#          {
#             'title': 'Smart Intro - KwikSchools',
#             'youtube_url': 'https://www.youtube.com/watch/lMgWQgFQrrY',
#             'description': 'A Smart Intro To KwikSchools.',
#             'is_staff_only': False
#         },
#         # Add more videos here
#         {
#             'title': 'A KwikSchools Quick Guide',
#             'youtube_url': 'https://www.youtube.com/watch/KwjiFOwDOl4',
#             'description': 'A walk-through video on how to use the features.',
#             'is_staff_only': False
#         },
#         {
#             'title': 'Admin - School Set-Up (Admin)',
#             'youtube_url': 'https://www.youtube.com/watch/dGpsPRIlkH4',
#             'description': 'Set Up - Initial portal set up',
#             'is_staff_only': True  # This video is for staff only
#         },
#          {
#             'title': 'Admin - Payment Module 1 (Admin)',
#             'youtube_url': 'https://www.youtube.com/watch/_DeB_8i-3jc',
#             'description': 'Set Up - Payment Module',
#             'is_staff_only': True  # This video is for staff only
#         },
#          {
#             'title': 'Admin - Student Enrolment & Teachers Signup',
#             'youtube_url': 'https://www.youtube.com/watch/EHOePJXKWp0',
#             'description': 'Set Up - Initial portal set up',
#             'is_staff_only': True  # This video is for staff only
#         },
#          {
#             'title': 'Admin - Assign Form Teachers To Classes',
#             'youtube_url': 'https://www.youtube.com/watch/jnm5nk58L-Q',
#             'description': 'How to assign form teachers to classes',
#             'is_staff_only': True  # This video is for staff only
#         },
#         {
#             'title': 'STUDENTS - The Student Dashboard 1',
#             'youtube_url': 'https://www.youtube.com/watch/xK9He7qwJLE',
#             'description': 'Exploring the student dashboard',
#             'is_staff_only': False  # This video is for staff only
#         },
#         {
#             'title': 'TEACHERS - The Teachers Dashboard 1',
#             'youtube_url': 'https://www.youtube.com/watch/HiRL_cLb8Z8',
#             'description': 'Exploring the teachers dashboard',
#             'is_staff_only': False  # This video is for staff only
#         },
       
#     ]

#     # Filter videos based on the user's staff status
#     if request.user.is_staff:
#         # Staff users see all videos
#         visible_videos = video_list
#     else:
#         # Non-staff users only see videos that are NOT staff only
#         visible_videos = [video for video in video_list if not video['is_staff_only']]

#     context = {
#         'title': 'Kwikschools Video Guides',
#         'videos': visible_videos,
#     }
#     return render(request, 'pages/video_guides.html', context)


# # NEWSLETTER LOGIC

# def send_newsletter_task(newsletter_id):
#     newsletter = Newsletter.objects.get(id=newsletter_id)
#     subject = newsletter.subject
    
#     # 1. Determine the Recipients
#     users = User.objects.filter(is_active=True)
    
#     if newsletter.target_audience == 'PARENTS':
#         users = users.filter(parent__isnull=False)
#     elif newsletter.target_audience == 'STUDENTS':
#         users = users.filter(student__isnull=False)
#     elif newsletter.target_audience == 'STAFF':
#         users = users.filter(teacher__isnull=False)
#     elif newsletter.target_audience == 'ADMINS':
#         users = users.filter(is_staff=True)
    
#     recipient_list = users.values_list('email', flat=True)

#     # 2. Prepare the Email Template
#     # You can reuse a professional wrapper template
#     html_content = render_to_string('emails/newsletter_template.html', {
#         'message': newsletter.message,
#         'subject': newsletter.subject,
#     })
#     text_content = strip_tags(newsletter.message)

#     # 3. Send via Anymail (Efficiently)
#     for email in recipient_list:
#         if email:
#             msg = EmailMultiAlternatives(subject, text_content, None, [email])
#             msg.attach_alternative(html_content, "text/html")
#             msg.send()

#     newsletter.sent = True
#     newsletter.save()