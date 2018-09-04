from django.conf.urls import url
from faconstor.views import *
from django.conf import settings

urlpatterns = [
    url(r'^$', index, {'funid': '2'}),
    url(r'^test/$', test),
    url(r'^index/$', index, {'funid': '2'}),
    url(r'^get_process_rto/$', get_process_rto),

    # 用户登录
    url(r'^login/$', login),
    url(r'^userlogin/$', userlogin),
    url(r'^forgetPassword/$', forgetPassword),
    url(r'^resetpassword/([0-9a-zA-Z]{8}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{12})/$',
        resetpassword),
    url(r'^reset/$', reset),
    url(r'^password/$', password),
    url(r'^userpassword/$', userpassword),

    # 系统维护
    url(r'^organization/$', organization, {'funid': '61'}),
    url(r'^orgdel/$', orgdel),
    url(r'^orgmove/$', orgmove),
    url(r'^orgpassword/$', orgpassword),
    url(r'^group/$', group, {'funid': '62'}),
    url(r'^groupsave/$', groupsave),
    url(r'^groupdel/$', groupdel),
    url(r'^getusertree/$', getusertree),
    url(r'^groupsaveusertree/$', groupsaveusertree),
    url(r'^getfuntree/$', getfuntree),
    url(r'^groupsavefuntree/$', groupsavefuntree),
    url(r'^function/$', function, {'funid': '63'}),
    url(r'^fundel/$', fundel),
    url(r'^funmove/$', funmove),

    # 预案管理
    url(r'^script/$', script, {'funid': '32'}),
    url(r'^scriptdata/$', scriptdata),
    url(r'^scriptdel/$', scriptdel),
    url(r'^scriptsave/$', scriptsave),
    url(r'^scriptexport/$', scriptexport),
    url(r'^processconfig/$', processconfig, {'funid': '31'}),
    url(r'^processscriptsave/$', processscriptsave),
    url(r'^get_script_data/$', get_script_data),
    url(r'^remove_script/$', remove_script),
    url(r'^setpsave/$', setpsave),
    url(r'^custom_step_tree/$', custom_step_tree),
    url(r'^processconfig/$', processconfig, {'funid': '63'}),
    url(r'^del_step/$', del_step),
    url(r'^move_step/$', move_step),
    url(r'^get_all_groups/$', get_all_groups),
    url(r'^processdesign/$', process_design, {"funid": "33"}),
    url(r'^process_data/$', process_data),
    url(r'^process_save/$', process_save),
    url(r'^process_del/$', process_del),
    url(r'^verify_items_save/$', verify_items_save),
    url(r'^get_verify_items_data/$', get_verify_items_data),
    url(r'^remove_verify_item/$', remove_verify_item),

    # 切换演练
    url(r'^falconstorswitch/(?P<process_id>\d+)$', falconstorswitch, {'funid': '41'}),
    url(r'^falconstorswitchdata/$', falconstorswitchdata),
    url(r'^falconstorrun/$', falconstorrun),
    url(r'^falconstor/(\d+)/$', falconstor, {'funid': '49'}),
    url(r'^getrunsetps/$', getrunsetps),
    url(r'^falconstorcontinue/$', falconstorcontinue),
    url(r'^processsignsave/$', processsignsave),
    url(r'^get_current_scriptinfo/$', get_current_scriptinfo),
    url(r'^ignore_current_script/$', ignore_current_script),

    # 历史查询
    url(r'^custom_pdf_report/$', custom_pdf_report),
    url(r'^falconstorsearch/$', falconstorsearch, {'funid': '5'}),
    url(r'^falconstorsearchdata/$', falconstorsearchdata),

    # 其他
    url(r'^downloadlist/$', downloadlist, {'funid': '7'}),
    url(r'^download/$', download),

    # 邀请
    url(r'^invite/$', invite),
    url(r'^get_all_users/$', get_all_users),

]
