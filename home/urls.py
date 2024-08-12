from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from home import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='ind'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('accounts/', include('allauth.urls')),
    path('admin_home/', include([
        path('', views.admin_home, name='admin_home'),
        path('adv_req/', views.adv_req, name='adv_req'),
        path('action_adv/', views.action_adv, name='action_adv'),
        path('client_req/', views.client_req, name='client_req'),
        path('action_client/', views.action_client, name='action_client'),
        path('approved_advocates/', views.approved_advocates_list, name='approved_advocates_list'),
        path('delete-advocate/<int:u_id>/', views.delete_advocate, name='delete_advocate'),
        path('client_list/', views.client_list, name='client_list'),  
        path('admin_home/delete-client/<int:u_id>/', views.delete_client, name='delete_client'),
    ])),
    path('adv_home/', include([

        path('', views.adv_home, name='adv_home'),
        path('advocate/profile/', views.advocate_profile, name='advocate_profile'),
        path('advocate_profile_update/', views.advocate_profile_update, name='advocate_profile_update'),
        path('change_password_adv/', views.change_password_adv, name='change_password_adv'),
        path('select_category/', views.select_category, name='select_category'),
        path('add_case/', views.add_case, name='add_case'),
        path('advocate/requests/', views.client_requests, name='client_requests'),
         path('update-request-status/', views.update_request_status, name='update_request_status'),
    ])),
    path('client_home/', include([

        path('', views.client_home, name='client_home'),
        path('client_profile_view/', views.client_profile_view, name='client_profile_view'),
        path('client_profile_update/', views.client_profile_update, name='client_profile_update'),
        #path('advocates_display/',views.get_advocates, name='advocate_display'),
        path('advocates/', views.advocate_list, name='advocate_list'),
   # path('advocate/request/<int:advocate_id>/', views.request_advocate, name='request_advocate'),
       #path('advocate/details/<int:advocate_id>/', views.advocate_details, name='advocate_details'),
        path('send_request/', views.send_request, name='send_request'),
    
    path('check_request_status/', views.check_request_status, name='check_request_status'),


    ])),
    #path('search/', views.search_advocates, name='search_advocates'),
    path('password_reset/', views.password_reset, name='password_reset'),
    path('reset/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('change_password/', views.change_password, name='change_password'),

    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
