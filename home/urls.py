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
        path('admin/payment_history/', views.admin_payment_history, name='admin_payment_history'),
        path('ipc_section/', views.ipc_section, name='ipc_section'),
        path('ipc_remove/', views.ipc_remove, name='ipc_remove'),   
        path('ipc_bulk_delete/', views.ipc_bulk_delete, name='ipc_bulk_delete'),  # Add this line
    ])),
    path('adv_home/', include([

        path('', views.adv_home, name='adv_home'),
        path('advocate/profile/', views.advocate_profile, name='advocate_profile'),
        path('advocate_profile_update/', views.advocate_profile_update, name='advocate_profile_update'),
        path('change_password_adv/', views.change_password_adv, name='change_password_adv'),
        path('select_category/', views.select_category, name='select_category'),
        path('add_case/', views.add_case, name='add_case'),
        path('client_request/', views.client_request, name='client_request'),
        path('handle_case/<int:case_id>/<str:action>/', views.handle_case, name='handle_case'),
        path('view_client_details/<int:client_id>/', views.view_client_details, name='view_client_details'),
        path('view_client_basic_details/<int:client_id>/', views.view_client_basic_details, name='view_client_basic_details'),
        path('view_case_details/<int:case_id>/', views.view_case_details, name='view_case_details'),
        path('advocate/client_previous_req/', views.client_previous_req, name='client_previous_req'),
        path('advocate/payment_history/', views.advocate_payment_history, name='advocate_payment_history'),
        path('advocate/view_feedback//', views.view_feedback, name='view_feedback'),
path('adv_home/advocate/<int:advocate_id>/client/<int:client_id>/appointments/', views.manage_appointments, name='view_appointments'),
    path('appointment/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('appointment/reschedule/<int:appointment_id>/', views.reschedule_appointment, name='reschedule_appointment'),
        path('appointment/request/reschedule/<int:appointment_id>/', views.request_reschedule_appointment, name='request_reschedule_appointment'),

        path('client_list/', views.client_list, name='client_list'),
        path('view_client_details/<int:client_id>/', views.view_client_details, name='view_client_details'),
        path('document-classification/', views.document_classification, name='document_classification'),
    #path('adv_home/classify/', classify_case, name='document_classification'),

    ])),
    path('client_home/', include([
        path('', views.client_home, name='client_home'),
        path('client_profile_view/', views.client_profile_view, name='client_profile_view'),
        path('client_profile_update/', views.client_profile_update, name='client_profile_update'),
        #path('advocates_display/',views.get_advocates, name='advocate_display'),
        path('advocates/', views.advocate_list, name='advocate_list'),
    path('advocate_profile/<int:advocate_id>/', views.view_advocate_profile, name='advocate_profile_view'),
    path('advocate/<int:advocate_id>/register_case/', views.register_case, name='register_case'),
        path('accepted_advocate_profile/<int:advocate_id>/', views.view_advocate_profile, name='accepted_advocate_profile_view'),
path('advocate/<int:advocate_id>/feedback/', views.feedback, name='feedback'),
        path('advocate/<int:advocate_id>/submit_feedback/', views.submit_feedback, name='submit_feedback'),
    #path('advocate/<int:advocate_id>/process_payment/', views.process_payment, name='process_payment'),
    path('advocate/<int:advocate_id>/book_appointment/', views.book_appointment, name='book_appointment'),
    path('advocate/<int:advocate_id>/appointments/', views.view_appointments, name='view_appointments'),
path('appointment/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),


        #path('payment_success/', views.payment_success, name='payment_success'),  # Add this line
        path('payment/<int:advocate_id>/', views.payment_view, name='payment'),
        path('payment/success/', views.payment_success, name='payment_success'),
        path('client/payment_history/', views.client_payment_history, name='client_payment_history'),
    path('client/advocate-list/', views.advocate_list_for_client, name='advocate_list_for_client'),
    path('client/payment_history/', views.client_payment_history, name='client_payment_history'),
    path('ipc_search/', views.ipc_search, name='ipc_search'),        
    ])),
    #path('search/', views.search_advocates, name='search_advocates'),
    path('password_reset/', views.password_reset, name='password_reset'),
    path('reset/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('change_password/', views.change_password, name='change_password'),

    #path('send_message/', send_message, name='send_message'),
    #path('get_chat_history/<int:other_user_id>/', get_chat_history, name='get_chat_history'),
    path('chat/<int:client_id>/<int:advocate_id>/', views.chat_view, name='chat'),


    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)