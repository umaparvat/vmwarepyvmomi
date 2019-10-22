import ssl
import atexit
import sys
import time
from pyVmomi import vim, vmodl
from pyVim import connect, task
from pyVim.connect import Disconnect
context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
context.verify_mode = ssl.CERT_NONE
srv_inst = connect.SmartConnect(host='vcsa-01a.corp.local', user='administrator@corp.local', pwd='VMware1!', port=443, sslContext= context)
content = srv_inst.RetrieveContent()
def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break
    return obj

allsw=[item for item in  content.viewManager.CreateContainerView(content.rootFolder, [vim.DistributedVirtualSwitch], True).view]  
allpg=[item for item in  content.viewManager.CreateContainerView(content.rootFolder, [vim.DistributedVirtualPortgroup], True).view]      

dvs = get_obj(content, [vim.DistributedVirtualSwitch], 'RegionA01-vDS-COMP')


#switch and portgroup selection
selection_set=[]
dvs_set=vim.dvs.DistributedVirtualSwitchSelection()
dvs_set.dvsUuid = dvs.uuid
selection_set.append(dvs_set)
dvs_ss = vim.dvs.DistributedVirtualPortgroupSelection()
dvs_ss.dvsUuid = dvs.uuid
for pg in dvs.portgroup:
    dvs_ss.portgroupKey.append(pg.key)
    selection_set.append(dvs_ss)

bkp = content.dvSwitchManager.DVSManagerExportEntity_Task(selection_set)
result = bkp.info.result

#to restore the switch and portgroup changes
entity_restore_config = content.dvSwitchManager.DVSManagerImportEntity_Task(result, 'applyToEntitySpecified')   
#to check status
entity_restore_config.info.state
entity_restore_config.info.error
#to check output
entity_restore_config.info.result

#### switch and portgroup new creation without hostmember #####

dvs_set=vim.dvs.DistributedVirtualSwitchSelection()
dvs_set.dvsUuid = dvs.uuid
selection_set=[]
selection_set.append(dvs_set)
dvs_ss = vim.dvs.DistributedVirtualPortgroupSelection()
dvs_ss.dvsUuid = dvs.uuid
for pg in dvs.portgroup:
    dvs_ss.portgroupKey.append(pg.key)
    selection_set.append(dvs_ss)
bkps = content.dvSwitchManager.DVSManagerExportEntity_Task(selection_set)
res_switch=bkps.info.result
# change the switch name, since the first is switch in the res_switch list
res_switch[0].name = res_switch[0].name+"-new" 
#create a new switch
 entity_restore_config = content.dvSwitchManager.DVSManagerImportEntity_Task([res_switch[0]], 'createEntityWithNewIdentifier')
 entity_restore_config.info.result
 # output , the new switch id
 (vim.dvs.DistributedVirtualSwitchManager.ImportResult) {
   dynamicType = <unset>,
   dynamicProperty = (vmodl.DynamicProperty) [],
   distributedVirtualSwitch = (vim.DistributedVirtualSwitch) [
      'vim.dvs.VmwareDistributedVirtualSwitch:dvs-338'
   ],
   distributedVirtualPortgroup = (vim.dvs.DistributedVirtualPortgroup) [],
   importFault = (vim.fault.ImportOperationBulkFault.FaultOnImport) []
}
 
# store the Importentity result into a variable    
switch_new=entity_restore_config.info.result
switch_new.distributedVirtualSwitch[0]
#output
'vim.dvs.VmwareDistributedVirtualSwitch:dvs-338'
 
 # change the portgroup backup with new switch info, since res_switch[0] is switch, taking from portgroup
result = []
for each_port_config in res_switch[1:]:
    each_port_config.name=each_port_config.name+"-new"
    each_port_config.container = switch_new.distributedVirtualSwitch[0]
    result.append(each_port_config)
    
 #to create new portgroups on the new switch 
entity_restore_port_config = content.dvSwitchManager.DVSManagerImportEntity_Task(result, 'createEntityWithNewIdentifier')   
 #to check status
entity_restore_port_config.info.state
entity_restore_port_config.info.error
#to check output
entity_restore_port_config.info.result  
