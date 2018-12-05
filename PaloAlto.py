#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import json
import urllib
import logging 
from lxml import etree
from xml.etree.ElementTree import fromstring
from json import dumps

# no warning from autosigned ssl 
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# class
class PaloAlto:
    def __init__(self, ip, key, **kwargs):
        self.vsys       = kwargs.get('vsys')
        self.dev_grp    = kwargs.get('device_group')
        self.shared     = kwargs.get('shared')
        self.log        = kwargs.get('log')

        if self.log : logging.basicConfig(filename='PaloAlto.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S ')

        # URL definition
        if self.vsys:
            self.path = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='" + self.vsys + "']"
        elif self.dev_grp:
            self.path = "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='" + self.dev_grp + "']"
        elif self.shared:
            self.path = "/config/shared"
        else: 
            print ("No target specified (either vsys, device_group or shared) : exiting")
            return
        
        self.api_get_config = 'https://' + ip + "/api/?type=config&action=get&" + "Key=" + key + "&"
        self.api_get_op     = 'https://' + ip + "/api/?type=op&" + "Key=" + key + "&"
        self.api_set        = 'https://' + ip + "/api/?type=config&action=set&" + "Key=" + key + "&"
        self.api_del        = 'https://' + ip + "/api/?type=config&action=delete&" + "Key=" + key + "&"

    def __ApiGetConfig(self, param):
        # configuration commands
       	if isinstance(param, str) : 
            req = requests.get(self.api_get_config + param, verify=False)
        else:

            req = requests.get(self.api_get_config + urllib.urlencode(param), verify=False)
        return req

    def __ApiGetOp(self, param):
        # operational commands
        print(param)
       	req = requests.get(self.api_get_op + urllib.urlencode(param), verify=False)
        print(req.url)
        return req

    def __ApiSet(self, param):
       	req = requests.get(self.api_set + urllib.urlencode(param), verify=False)
        return req.status_code
    
    def __ApiDel(self, param):
       	req = requests.get(self.api_del + urllib.urlencode(param), verify=False)
        return req.status_code
    
    #-----------------------------------------------------------------------------------------

    def Commit(self):
        """
        Commit configuration to the fw.

        Returns
        -------
        Http status code: 200 if ok, 4xx if an error occurs
        """
        param   = "cmd=<commit></commit>"
        req     = self.__ApiGetConfig(param)
        
        if self.log : logging.info('commit')
        return req

    def GetUrlCategory(self, category_name):
        """
        Get url member list of a category.

        Parameters
        ---------- 
        category_name : the category name (type str)
        url           : the url to add (type str)

        Returns
        -------
        Json object : { "url": ["xx","yy"], "name":"xx" }
        """
        param   = {'xpath': self.path + "/profiles/custom-url-category/entry[@name='" + category_name + "']/list"}
        req     = self.__ApiGetConfig(param)
    
        contents = etree.fromstring(req.text)
        results = {}
        results['name'] = category_name
        results['url'] = []
        for i in contents[0]:
            if i.tag == 'list':
                for j in i:
                    results['url'].append(j.text)

        return dumps(results, indent=3)

    def AddUrlCategory(self, category_name):
        """
        Create an empty url category.
        
        Parameters
        ----------
        category_name : category name (type string)

        Returns
        -------
        Http status code: 200 if ok, 4xx if an error occurs
        """
        param   = {
            'xpath':  self.path + "/profiles/custom-url-category/entry[@name='" + category_name + "']",
            'element':"<description> </description>"
            }
        req     = self.__ApiSet(param)

        if self.log : logging.info('add url category: ' + category_name)
        return req

    def DelUrlCategory(self, category_name):
        """
        Delete an url category.

        Parameters
        ---------- 
        category_name : category name (type string)

        Returns
        -------
        Http status code: 200 if ok, 4xx if an error occurs
        """
        param   = {'xpath': self.path + "/profiles/custom-url-category/entry[@name='" + category_name + "']"}
        req     = self.__ApiDel(param)

        if self.log : logging.info('del url category: ' + category_name )
        return req

    def AddUrlToCategory(self, category_name, url):
        """
        Add url to an existing category object.

        Parameters
        ---------- 
        category_name : the category name (type str)
        url           : the url to add (type str)

        Returns
        -------
        Http status code: 200 if ok, 4xx if an error occurs
        """
        param   = {
            'xpath'  : self.path + "/profiles/custom-url-category/entry[@name='" + category_name + "']/list",
            'element':"<member>" + url + "</member>"
            }
        req     = self.__ApiSet(param)

        if self.log : logging.info('add url: ' + url + ' to category: ' + category_name)
        return req

    def DelUrlFromCategory(self, category_name, url):
        """
        Delete an url from an existing category object.

        Parameters
        ---------- 
        category_name : the category name (type str)
        url           : the url to add (type str)

        Returns
        -------
        Http status code: 200 if ok, 4xx if an error occurs
        """
        param   = {'xpath': self.path + "/profiles/custom-url-category/entry[@name='" + category_name + "']/list/member[text()='" + url + "']"}
        req     = self.__ApiDel(param)

        if self.log : logging.info('del url: ' + url + ' from category: ' + category_name)
        return req

    def GetService(self, service_name):
        """
        Get an service object by name.

        Parameters
        ----------
        service_name    : the address object name ( type str)

        Returns
        -------
        Json object : {"protocol": "tcp/udp", "port": "xx"}
        """
        param   = { 'xpath':  self.path + "/service/entry[@name='" + service_name + "']" }
        req     = self.__ApiGetConfig(param)
        
        result = {}
        tree = etree.fromstring(req.text)
        node = tree.xpath("/response/result/entry/protocol")
        try:
            protocol = node[0][0].tag
            result['protocol'] = protocol
        except:
            return
        node = tree.xpath("/response/result/entry/protocol/" + protocol + "/port")
        result['port'] = node[0].text

        return dumps(result, indent=3)

    def GetService(self, protocol, port):
        """
        Get an service object by protocol and port.

        Parameters
        ----------
        protocol : tpc/udp ( type str)
        port     : (type int)

        Returns
        -------
        Json object : {"name": "xx"}
        """
        param   = { 'xpath':  self.path + "/service" }
        req     = self.__ApiGetConfig(param)
        
        result = {}
        tree = etree.fromstring(req.text)

        for i in tree[0][0]:
            if i[0][0].tag == protocol:
                for j in i[0][0]:
                    if j.tag == 'port' and j.text == port:
                        result['name'] = i.attrib['name']

        return dumps(result, indent=3)

    def AddService(self, protocol, port, service_name=''):
        """
        Add a new service object.

        Parameters
        ----------
        protocol     : tcp/udb/icmp (type str)
        port         : the port number (type int)
        service_name : the service name (optional (will be set to protocol_port if not present), type str)

        Returns
        -------
        Http status code: 200 if ok, 4xx if an error occurs
        """
        if not service_name : 
            service_name = protocol + '_' + str(port)
        param   = {
            'xpath':  self.path + "/service/entry[@name='" + service_name + "']/protocol/tcp",
            'element':"<port>" + str(port) + "</port>"
            }
        req     = self.__ApiSet(param)

        if self.log : logging.info('add service: ' + service_name + ' : ' + protocol + ':' + str(port))
        return req

    def DelService(self, service_name):
        """
        Delete an service object.

        Parameters
        ---------- 
        service_name : the service object name ( type str)

        Returns
        -------
        Http status code: 200 if ok, 4xx if an error occurs
        """
        param   = {'xpath': self.path + "/service/entry[@name='" + service_name + "']"}
        req     = self.__ApiDel(param)

        if self.log : logging.info('del service: ' + service_name )
        return req

    def GetAddressName(self, ip, withNetmask=False):
        """
        Get Name of the object with the given IP Address.

        Parameters
        ----------
        ip : IP (type str)
        withNetmask : append '/32' to the object's ip (type bool, default False)
 
        Returns
        -------
        Json object : {"name": "xx"}
        """
        param   = {'xpath':  self.path + "/address"}
        req     = self.__ApiGetConfig(param)

        tree = etree.fromstring(req.text)
        ipName = tree.find("./result/address/entry/[ip-netmask='"+ ip +"']")

        if ipName is not None:
            return dumps({"name": ipName.attrib.get("name")})
        
        if withNetmask:
            return self.GetAddressName(ip + '/32')

        return {}

    def GetAddress(self, address_name):
        """
        Get an address object.

        Parameters
        ----------
        address_name : the address object name (type str)

        Returns
        -------
        Json object : {"type":"ip-netmask/ip-range/fqdn", "address": "xx"}
        """
        param   = { 'xpath':  self.path + "/address/entry[@name='" + address_name + "']" }
        req     = self.__ApiGetConfig(param)
        
        print(req.text)

        tree = etree.fromstring(req.text)
        node = tree.xpath("/response/result/entry")
        try:
            address_type = node[0][0].tag
            address      = node[0][0].text
            return dumps({'type': address_type, 'address': address }, indent=3)
        except:
            pass

        return {}

    def AddAddress(self, address_name, ip):
        """
        Add a new address object.

        Parameters
        ----------
        address_name : the address object name ( type str)
        ip           : ip address (type string)

        Returns
        -------
        Http status code: 200 if ok, 4xx if an error occurs
        """
        param   = {
            'xpath':  self.path + "/address/entry[@name='" + address_name + "']",
            'element':"<ip-netmask>" + ip + "</ip-netmask>"
            }
        req     = self.__ApiSet(param)

        if self.log : logging.info('add address: ' + address_name + ' : ' + ip)
        return req

    def DelAddress(self, address_name):
        """
        Delete an address object.

        Parameters
        ---------- 
        address_name : the address object name ( type str)

        Returns
        -------
        Http status code: 200 if ok, 4xx if an error occurs
        """
        param   = {'xpath': self.path + "/address/entry[@name='" + address_name + "']"}
        req     = self.__ApiDel(param)

        if self.log : logging.info('del address: ' + address_name )
        return req

    def GetAddressGroup(self, group_name):
        """
        Get an address group object.

        Parameters
        ----------
        group_name : the address object group name ( type str)

        Returns
        -------
        Json object : { "addresses": ["xx","yy"], "name":"xx" }
        """
        param   = { 'xpath': self.path + "/address-group/entry[@name='" + name + "']/static" }
        req     = self.__ApiGetConfig(param)

        contents = etree.fromstring(req.text)
        results = {}
        results['name'] = group_name
        results['addresses'] = []
        for i in contents[0]:
            if i.tag == 'static':
                for j in i:
                    results['addresses'].append(j.text)

        return dumps(results, indent=3)

    def AddAddressGroup(self, group_name):
        """
        Create an empty address group.
        
        Parameters
        ----------
        group_name : (type string)

        Returns
        -------
        Http status code: 200 if ok, 4xx if an error occurs
        """
        param   = {
            'xpath':  self.path + "/address-group/entry[@name='" + group_name + "']",
            'element':"<description> </description>"
            }
        req     = self.__ApiSet(param)

        if self.log : logging.info('add address group: ' + group_name)
        return req

    def DelAddressGroup(self, group_name):
        """
        Delete an address group object.

        Parameters
        ---------- 
        group_name : the address group object name ( type str)

        Returns
        -------
        Http status code: 200 if ok, 4xx if an error occurs
        """
        param   = {'xpath': self.path + "/address-group/entry[@name='" + group_name + "']"}
        req     = self.__ApiDel(param)

        if self.log : logging.info('del address group: ' + group_name )
        return req

    def AddAddressToGroup(self, group_name, address_name):
        """
        Add an address to a group.
        If the group does not exists, it will be created.
        Otherwise the address object will be added to the group.

        Parameters
        ----------
        group_name   : (type string)
        address_name : an address object name (type string)

        Returns
        -------
        Http status code: 200 if ok, 4xx if an error occurs
        """
        param   = {
            'xpath':  self.path + "/address-group/entry[@name='" + group_name + "']/static",
            'element':"<member>" + address_name + "</member>"
            }
        req     = self.__ApiSet(param)

        if self.log : logging.info('add address: ' + address_name + ' to group ' + group_name)
        return req
    
    def DelAddressFromGroup(self, group_name, address_name):
        """
        Delete an address from a group.
        
        Parameters
        ----------
        group_name   : (type string)
        address_name : an address object name (type string)
         
        Returns
        -------
        Http status code: 200 if ok, 4xx if an error occurs
        """
        param   = {'xpath':  self.path + "/address-group/entry[@name='" + group_name + "']/static/member[text()='" + address_name + "']"}
        req     = self.__ApiDel(param)

        if self.log : logging.info('del address: ' + address_name + ' from group ' + group_name)
        return req

    def GetPreRule(self, pre_rule_name):
        """
        Parameters
        ----------
        pre_rule_name : the prerule name (type str)

        Returns
        -------
        Json object
        ex:
            {
            "category": "any",
            "application": "any",
            "from": "any",
            "target": "no",
            "service": [
                "UDP_514",
                "UDP_20514"
            ],
            "to": "any",
            "destination": [
                "logpoint",
                "nte-sh-radius1"
            ],
            "disabled": "no",
            "source": [
                "fw-palo-panorama",
                "grp-opt-riverbed",
                "grp-switch"
            ],
            "source-user": "any",
            "tag": [
                "flux technique",
                "paloalto"
            ],
            "hip-profiles": "any",
            "action": "allow",
            "log-setting": "default",
            "name": "flux syslog"
            }
        """
        param   = {'xpath': self.path + "/pre-rulebase/security/rules/entry[@name=\'" + pre_rule_name + "\']"}
        req     = self.__ApiGetConfig(param)

        contents = etree.fromstring(req.text)
        # 2DO correct this
        if contents is None : return {}

        results = {}
        results['source'] = []
        results['destination'] = []
        results['service'] = []
        results['tag'] = []
        for i in contents[0][0]:
            if i.tag == 'source':
                for j in i:
                    results['source'].append(j.text)
            elif i.tag == 'destination':
                for j in i:
                    results['destination'].append(j.text)
            elif i.tag == 'tag':
                for j in i:
                    results['tag'].append(j.text)
            elif i.tag == 'service':
                for j in i:
                    results['service'].append(j.text)
            else:
                try:
                    results[i.tag] = i[0].text
                except :
                    results[i.tag] = i.text
        results['name'] = pre_rule_name

        return dumps(results, indent=3)

def Vsys(ip, key, vsys, log=False):
    return PaloAlto(ip, key, vsys=vsys, log=log)

def Shared(ip, key, log=False):
    return PaloAlto(ip, key, shared=True, log=log)

def DeviceGroup(ip, key, device_group, log=False):
    return PaloAlto(ip, key, device_group=device_group, log=log)


#-----------------------------------------------------------------
def dump(obj):
  for attr in dir(obj):
    print("obj.%s = %r" % (attr, getattr(obj, attr)))
