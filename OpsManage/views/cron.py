#!/usr/bin/env python  
# _#_ coding:utf-8 _*_  
import os,uuid
from django.http import HttpResponseRedirect,JsonResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from OpsManage.models import Cron_Config,Server_Assets
from OpsManage.utils.ssh_tools import SSHManage
from OpsManage.utils import base
from OpsManage.tasks import recordCron
from OpsManage.models import Log_Cron_Config
from django.contrib.auth.decorators import permission_required
from OpsManage.utils.ansible_api_v2 import ANSRunner
from OpsManage.data.DsRedisOps import DsRedis
from django.conf import settings

@login_required()
@permission_required('OpsManage.can_add_cron_config',login_url='/noperm/') 
def cron_add(request):
    serverList = Server_Assets.objects.all()
    if request.method == "GET": 
        return render_to_response('cron/cron_add.html',{"user":request.user,"serverList":serverList},
                                  context_instance=RequestContext(request))
    elif request.method == "POST":
        cron_status = request.POST.get('cron_status',0)
        try:
            server = Server_Assets.objects.get(id=request.POST.get('cron_server'))
        except:
            return render_to_response('cron/cron_add.html',{"user":request.user,
                                                               "serverList":serverList,
                                                               "errorInfo":"主机不存在，请检查是否被删除。"},
                                  context_instance=RequestContext(request)) 
        try:
            cron = Cron_Config.objects.create(
                                       cron_minute=request.POST.get('cron_minute'),
                                       cron_hour=request.POST.get('cron_hour'),
                                       cron_day=request.POST.get('cron_day'),
                                       cron_week=request.POST.get('cron_week'),
                                       cron_month=request.POST.get('cron_month'),
                                       cron_user=request.POST.get('cron_user'),
                                       cron_name=request.POST.get('cron_name'),
                                       cron_desc=request.POST.get('cron_desc'),
                                       cron_server=server,
                                       cron_command=request.POST.get('cron_command'),
                                       cron_script=request.FILES.get('cron_script', None),
                                       cron_script_path=request.POST.get('cron_script_path',None),
                                       cron_status=cron_status,
                                       )
            recordCron.delay(cron_user=str(request.user),cron_id=cron.id,cron_name=cron.cron_name,cron_content="添加计划任务",cron_server=server.ip)
        except Exception,e:
            return render_to_response('cron/cron_add.html',{"user":request.user,
                                                               "serverList":serverList,
                                                               "errorInfo":"提交失败，错误信息："+str(e)},
                                  context_instance=RequestContext(request))    
        
        if  int(cron_status) == 1: 
            try:
                sList = [server.ip]
                if server.keyfile == 1:resource = [{"hostname": server.ip, "port": int(server.port)}] 
                else:resource = [{"hostname": server.ip, "port": int(server.port),"username": server.username,"password": server.passwd}]              
                ANS = ANSRunner(resource)
                if cron.cron_script:
                    src = settings.MEDIA_ROOT + '/' + str(cron.cron_script)
                    file_args = """src={src} dest={dest} owner={user} group={user} mode=755""".format(src=src,dest=cron.cron_script_path,user=cron.cron_user)
                    ANS.run_model(host_list=sList,module_name="copy",module_args=file_args)        
                    result = ANS.handle_model_data(ANS.get_model_result(), 'copy',file_args)  
                if result[0].get('status') != 'failed':
                    cron_args = """name={name} minute='{minute}' hour='{hour}' day='{day}'
                                   weekday='{weekday}' month='{month}' user='{user}' job='{job}'""".format(name=cron.cron_name,minute=cron.cron_minute,
                                                                                                        hour=cron.cron_hour,day=cron.cron_day,
                                                                                                         weekday=cron.cron_week,month=cron.cron_month,
                                                                                                         user=cron.cron_user,job=cron.cron_command
                                                                                                         )  
                    ANS.run_model(host_list=sList,module_name="cron",module_args=cron_args)    
                    result = ANS.handle_model_data(ANS.get_model_result(), 'cron',cron_args) 
            except Exception,e:
                return render_to_response('cron/cron_add.html',{"user":request.user,
                                                                   "serverList":serverList,
                                                                   "errorInfo":"错误信息:"+str(e)}, 
                                      context_instance=RequestContext(request))     
            if result[0].get('status') == 'failed':
                cron.delete()
                return render_to_response('cron/cron_add.html',{"user":request.user,
                                                                   "serverList":serverList,
                                                                   "errorInfo":"错误信息:"+result[0].get('msg')}, 
                                      context_instance=RequestContext(request)) 
        return HttpResponseRedirect('/cron_add')

@login_required()
@permission_required('OpsManage.can_read_config',login_url='/noperm/') 
def cron_list(request):
    cronList = Cron_Config.objects.select_related().all()
    return render_to_response('cron/cron_list.html',{"user":request.user,
                                                    "cronList":cronList},
                              context_instance=RequestContext(request)) 
    
@login_required()
@permission_required('OpsManage.can_change_cron_config',login_url='/noperm/') 
def cron_mod(request,cid): 
    try:
        cron = Cron_Config.objects.select_related().get(id=cid)
    except:
        return render_to_response('cron/cron_modf.html',{"user":request.user,
                                                         "errorInfo":"任务不存在，可能已经被删除."},
                                context_instance=RequestContext(request))    
    if request.method == "GET": 
        return render_to_response('cron/cron_modf.html',
                                  {"user":request.user,"cron":cron},
                                context_instance=RequestContext(request)) 
    elif request.method == "POST":    
        try:
            Cron_Config.objects.filter(id=cid).update(
                       cron_minute=request.POST.get('cron_minute'),
                       cron_hour=request.POST.get('cron_hour'),
                       cron_day=request.POST.get('cron_day'),
                       cron_week=request.POST.get('cron_week'),
                       cron_month=request.POST.get('cron_month'),
                       cron_user=request.POST.get('cron_user'),
                       cron_desc=request.POST.get('cron_desc'),
                       cron_command=request.POST.get('cron_command'),
                       cron_script_path=request.POST.get('cron_script_path',None),
                       cron_status=request.POST.get('cron_status'),
                                       )
            recordCron.delay(cron_user=str(request.user),cron_id=cid,cron_name=cron.cron_name,cron_content="修改计划任务",cron_server=cron.cron_server.ip)
        except Exception,e:
            return render_to_response('cron/cron_modf.html',
                                      {"user":request.user,"errorInfo":"更新失败，错误信息："+str(e)},
                                  context_instance=RequestContext(request))  
        try:
            sList = [cron.cron_server.ip]
            if cron.cron_server.keyfile == 1:resource = [{"hostname": cron.cron_server.ip, "port": int(cron.cron_server.port)}] 
            else:resource = [{"hostname": cron.cron_server.ip, "port": int(cron.cron_server.port),
                         "username": cron.cron_server.username,"password": cron.cron_server.passwd}]    
            cron = Cron_Config.objects.get(id=cid)
            if request.FILES.get('cron_script'):
                cron.cron_script=request.FILES.get('cron_script')
                cron.save()
            ANS = ANSRunner(resource)
            if  cron.cron_status == 0:ANS.run_model(host_list=sList,module_name="cron",module_args="""name={name} state=absent""".format(name=cron.cron_name))       
            else:
                if cron.cron_script:
                    src = os.getcwd() + '/' + str(cron.cron_script)
                    file_args = """src={src} dest={dest} owner={user} group={user} mode=755""".format(src=src,dest=cron.cron_script_path,user=cron.cron_user)
                    ANS.run_model(host_list=sList,module_name="copy",module_args=file_args)  
                cron_args = """name={name} minute='{minute}' hour='{hour}' day='{day}'
                               weekday='{weekday}' month='{month}' user='{user}' job='{job}'""".format(name=cron.cron_name,minute=cron.cron_minute,
                                                                                                    hour=cron.cron_hour,day=cron.cron_day,
                                                                                                     weekday=cron.cron_week,month=cron.cron_month,
                                                                                                     user=cron.cron_user,job=cron.cron_command
                                                                                                     )                              
                ANS.run_model(host_list=sList,module_name="cron",module_args=cron_args)    
        except Exception,e:
            return render_to_response('cron/cron_modf.html',{"user":request.user,"errorInfo":"错误信息:"+str(e)}, 
                                  context_instance=RequestContext(request))                     
        return HttpResponseRedirect('/cron_mod/{id}/'.format(id=cid))
    
    elif request.method == "DELETE":      
        try:
            recordCron.delay(cron_user=str(request.user),cron_id=cid,cron_name=cron.cron_name,cron_content="删除计划任务",cron_server=cron.cron_server.ip)
            sList = [cron.cron_server.ip]
            if cron.cron_server.keyfile == 1:resource = [{"hostname": cron.cron_server.ip, "port": int(cron.cron_server.port)}] 
            else:resource = [{"hostname": cron.cron_server.ip, "port": int(cron.cron_server.port),
                         "username": cron.cron_server.username,"password": cron.cron_server.passwd}]    
            ANS = ANSRunner(resource)  
            ANS.run_model(host_list=sList,module_name="cron",module_args="""name={name} state=absent""".format(name=cron.cron_name))    
            cron.delete()      
        except Exception,e:
            return JsonResponse({'msg':'删除失败：'+str(e),"code":500,'data':[]})                
        return JsonResponse({'msg':'删除成功',"code":200,'data':[]})       
        
@login_required()
@permission_required('OpsManage.can_add_cron_config',login_url='/noperm/') 
def cron_config(request):
    serverList = Server_Assets.objects.all()
    if request.method == "GET": 
        return render_to_response('cron/cron_config.html',{"user":request.user,"serverList":serverList},
                                  context_instance=RequestContext(request))    
    elif request.method == "POST": 
        try:
            server = Server_Assets.objects.get(id=request.POST.get('cron_server'))
        except:
            return JsonResponse({'msg':"主机资源不存在","code":500,'data':[]})  
        try:
            repeatCron = ""
            for ds in request.POST.get('cron_data').split('\n'):
                cron = ds.split('|')
                cron_name = cron[0]
                cron_time = cron[1]
                cron_data = cron_time.split(' ',5)
                try:
                    cron = Cron_Config.objects.create(
                                               cron_minute=cron_data[0],
                                               cron_hour=cron_data[1],
                                               cron_day=cron_data[2],
                                               cron_week=cron_data[3],
                                               cron_month=cron_data[4],
                                               cron_user=request.POST.get('cron_user'),
                                               cron_name=cron_name,
                                               cron_desc=cron_name,
                                               cron_server=server,
                                               cron_command=cron_data[5],
                                               cron_script=request.FILES.get('file', None),
                                               cron_status=request.POST.get('cron_status',0),
                                               )
                    recordCron.delay(cron_user=str(request.user),cron_id=cron.id,cron_name=cron.cron_name,cron_content="导入计划任务",cron_server=server.ip)
                    if  int(cron.cron_status) == 1: 
                        sList = [server.ip]
                        if server.keyfile == 1:resource = [{"hostname": server.ip, "port": int(server.port)}] 
                        else:resource = [{"hostname": server.ip, "port": int(server.port),"username": server.username,"password": server.passwd}]                
                        ANS = ANSRunner(resource)
                        ANS.run_model(host_list=sList,module_name="cron",module_args="""name={name} minute='{minute}' hour='{hour}' day='{day}'
                                                                                     weekday='{weekday}' month='{month}' user='{user}' job='{job}'""".format(name=cron.cron_name,minute=cron.cron_minute,
                                                                                                                                                         hour=cron.cron_hour,day=cron.cron_day,
                                                                                                                                                         weekday=cron.cron_week,month=cron.cron_month,
                                                                                                                                                         user=cron.cron_user,job=cron.cron_command
                                                                                                                                                         )
                                                                                     )                     
                except Exception,e:
                    repeatCron = cron_name + "<br>" + repeatCron 
        except:
            return JsonResponse({'msg':'数据格式不对',"code":500,'data':[]}) 
        if repeatCron:return JsonResponse({'msg':'添加失败，以下是重复内容：<br>' + repeatCron,"code":200,'data':[]}) 
        else:return JsonResponse({'msg':'添加成功',"code":200,'data':[]}) 
        
@login_required(login_url='/login')  
def cron_log(request):
    if request.method == "GET":
        cronList = Log_Cron_Config.objects.all().order_by('-id')[0:120]
        return render_to_response('cron/cron_log.html',{"user":request.user,"cronList":cronList},
                                  context_instance=RequestContext(request))


@login_required()
def cron_result(request, cid):
    if request.method == "POST":
        # print cid,type(cid)
        try:
            msg = DsRedis.OpsDeploy.rpop(request.POST.get('cron_uuid'))
        except Exception, e:
            print e
        if msg:
            return JsonResponse({'msg': msg, "code": 200, 'data': []})
        else:
            return JsonResponse({'msg': None, "code": 200, 'data': []})


@login_required()
@permission_required('OpsManage.can_add_cron_config', login_url='/noperm/')
def cron_file_distribution(request):
    serverList = Server_Assets.objects.all()
    cron_uuid = uuid.uuid4()
    # print serverList
    if request.method == "GET":
        return render_to_response('cron/cron_file_distribution.html', {"user": request.user, "serverList": serverList,
                                                                       "cron_uuid": cron_uuid},
                                  context_instance=RequestContext(request))


@login_required()
@permission_required('OpsManage.can_add_cron_config', login_url='/noperm/')
def cron_script_execution(request):
    if request.method == "GET":
        serverList = Server_Assets.objects.all()
        cron_uuid = uuid.uuid4()
        return render_to_response('cron/cron_script_execution.html', {"user": request.user, "serverList": serverList,
                                                                      "cron_uuid": cron_uuid},
                                  context_instance=RequestContext(request))
    elif request.method == "POST":
        script_mode = request.POST.get('cron_script_mode')
        cron_uuid = request.POST.get('cron_uuid')
        # print cron_uuid
        DsRedis.OpsDeploy.delete(cron_uuid)
        sList = []
        resource = []
        for server in request.POST.getlist('cron_server'):
            server_assets = Server_Assets.objects.get(ip=server)
            sList.append(server_assets.ip)
            if server_assets.keyfile == 1:
                resource.append({"hostname": server_assets.ip, "port": int(server_assets.port)})
            else:
                resource.append(
                    {"hostname": server_assets.ip, "port": int(server_assets.port), "username": server_assets.username,
                     "password": server_assets.passwd})
        # 执行ansible playbook
        if resource:
            try:
                ANS = ANSRunner(resource)
                DsRedis.OpsDeploy.lpush(cron_uuid, data="[Running]  Initial resource success")
            except Exception, err:
                print err
            if script_mode == '0':
                script_file = request.POST.get('script_file')
                dst_file = '/tmp' + os.sep + script_file.split('/')[-1]
                suffix_name = script_file.split('.')[-1]
                result = base.checkFile(script_file)
                if result[0] > 0:
                    print result[1]
                    return JsonResponse({'msg': result[1], "code": 500, 'data': []})
                try:
                    fileargs = '''src={srcDir} dest={desDir} '''.format(srcDir=script_file, desDir=dst_file)
                    ANS.run_model(host_list=sList, module_name='copy', module_args=fileargs)
                except Exception, err:
                    print err
                # 设置执行参数
                if suffix_name == 'sh':
                    raw_args = "/bin/bash " + dst_file
                elif suffix_name == 'py':
                    raw_args = "python " + dst_file
                elif suffix_name == 'pl':
                    raw_args = "perl " + dst_file
                else:
                    return JsonResponse({'msg': "不支持的脚本类型" + suffix_name, "code": 500, 'data': []})
            elif script_mode == '1':
                raw_args = request.POST.get('remote_command')
            else:
                print "not match type"
            
            # 执行远程命令
            try:
                ANS.run_model(host_list=sList, module_name='raw', module_args=raw_args)
                dataList = ANS.handle_model_data(ANS.get_model_result(), 'raw', module_args=raw_args)
                for ds in dataList:
                    DsRedis.OpsDeploy.lpush(cron_uuid, data='''[Running] Execute command:{command} to {host}
                                                         status: {status} msg: {msg}'''.format(host=ds.get('ip'),
                                                                                               status=ds.get('status'),
                                                                                               msg=ds.get('msg'),
                                                                                               command=raw_args))
                if ds.get('status') == 'failed': result = (1, "执行出错: " + ds.get('msg'))
            except Exception, err:
                print err
            DsRedis.OpsDeploy.lpush(cron_uuid, data="[Done] Excute Script Success.")
            # 记录日志
            recordCron.delay(cron_user=str(request.user), cron_id=0, cron_name=request.POST.get('cron_script_name'),
                             cron_content="执行命令成功," + raw_args, cron_server=",".join(sList))
            return JsonResponse({'msg': "快速脚本执行成功", "code": 200, 'data': ""})
        else:
            return JsonResponse({'msg': "初始化资源失败", "code": 500, 'data': []})


@login_required()
def cron_run(request, cid):
    if request.method == "POST":
        cron_file_name = request.POST.get('cron_file_name')
        cron_dstfile_name = request.POST.get('cron_dstfile_name')
        # 判断源文件是否存在
        try:
            result = base.checkFile(cron_file_name)
            if result[0] > 0:
                return JsonResponse({'msg': result[1], "code": 500, 'data': []})
        except Exception, e:
            return JsonResponse({'msg': e, "code": 500, 'data': []})
        if isinstance(cid, int):
            pass
        else:
            cron_uuid = cid
        # 清理旧rediskey，初始化inventor
        try:
            DsRedis.OpsDeploy.delete(cron_uuid)
            DsRedis.OpsDeploy.lpush(cron_uuid,
                                    data="[Start] Start file distribution，taskname:%s" % request.POST.get(
                                        'cron_job_name'))
        except Exception, e:
            print e
        sList = []
        resource = []
        serverList = request.POST.getlist('cron_server')
        # serverList = [Server_Assets.objects.get(ip=ds) for ds in request.POST.getlist('cron_server')]
        for server in serverList:
            server_assets = Server_Assets.objects.get(ip=server)
            sList.append(server_assets.ip)
            if server_assets.keyfile == 1:
                resource.append({"hostname": server_assets.ip, "port": int(server_assets.port)})
            else:
                resource.append(
                    {"hostname": server_assets.ip, "port": int(server_assets.port), "username": server_assets.username,
                     "password": server_assets.passwd})
        DsRedis.OpsDeploy.lpush(cron_uuid, data="[Running]  Initial resource success")
        # 执行ansible playbook
        fileargs = '''src={srcDir} dest={desDir} backup=yes'''.format(srcDir=cron_file_name,
                                                                      desDir=cron_dstfile_name)
        ANS = ANSRunner(resource)
        ANS.run_model(host_list=sList, module_name='copy', module_args=fileargs)
        # 获取结果
        dataList = ANS.handle_model_data(ANS.get_model_result(), 'copy', module_args=fileargs)
        for ds in dataList:
            DsRedis.OpsDeploy.lpush(cron_uuid, data='''[Running] sync {file} to {host}
                                    status: {status} msg: {msg}'''.format(host=ds.get('ip'), status=ds.get('status'),
                                                                          msg=ds.get('msg'), file=cron_file_name))
        if ds.get('status') == 'failed':
            result = (1, "部署错误: " + ds.get('msg'))
        if result[0] > 0:
            return JsonResponse({'msg': result[1], "code": 500, 'data': []})
        DsRedis.OpsDeploy.lpush(cron_uuid, data="[Done] Sync file Success.")
        # 记录日志
        recordCron.delay(cron_user=str(request.user), cron_id=0, cron_name=request.POST.get('cron_job_name'),
                         cron_content="分发文件任务,源文件%s,目标文件:%s" % (cron_file_name, cron_dstfile_name)
                         , cron_server=",".join(sList))
        return JsonResponse({'msg': "分发文件成功", "code": 200, 'data': ""})

