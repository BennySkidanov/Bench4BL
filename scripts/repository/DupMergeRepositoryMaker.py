#-*- coding: utf-8 -*-
'''
Created on 2016. 11. 19
Updated on 2016. 01. 09
'''

import cgi
import os
import re
import html
import codecs
import shutil
from functools import cmp_to_key

from commons import VersionUtil
from datetime import datetime
from bs4 import BeautifulSoup
from commons import Subjects


class DupMergeRepositoryMaker:
	'''
	'''
	__name__ = 'DupMergeRepositoryMaker'

	def __init__(self):
		pass

	def make(self, _group, _project):
		'''
		make repository files
		:param _group:
		:param _project:
		:return:
		'''
		self.S = Subjects()

		print('working with %s / %s' % (_group, _project))
		filename = os.path.join(self.S.getPath_bugrepo(_group, _project), 'repository.xml')
		bugs = self.load_bugs(filename)
		dups = self.S.duplicates[_project]

		merges = self.merge(_group, _project, bugs, dups)
		print('created %d merged reports.' % len(merges))

		versionItems = self.getItemsByVersion(merges, self.S.versions[_project].keys())
		print('created %d version repositories from merged reports.' % len(versionItems))

		print('storing....', end='')
		repositoryPath = os.path.join(self.S.getPath_bugrepo(_group, _project), 'repository_merge')
		if os.path.exists(repositoryPath) is True:
			shutil.rmtree(repositoryPath)
		if os.path.exists(repositoryPath) is False:
			os.makedirs(repositoryPath)

		self.outputXML(_project, merges, os.path.join(self.S.getPath_bugrepo(_group, _project), 'repository_merge.xml'))
		for ver in versionItems.keys():
			filename = os.path.join(repositoryPath, VersionUtil.get_versionName(ver, _project) + '.xml')
			self.outputXML(_project, versionItems[ver], filename)
		print('Done')

		answers = self.make_answers(_project, merges, versionItems)
		self.save_answers({_project:answers}, os.path.join(self.S.getPath_base(_group, _project), 'answers_merge.txt'))
		pass

	def make_answers(self, _project, _items, _versionItems):

		answers = {'all':{}}
		for item in _items:
			answers['all'][int(item['id'])] = len(item['fixedFiles'])

		for version in _versionItems:
			versionName = VersionUtil.get_versionName(version, _project)
			answers[versionName] = {}
			for item in _versionItems[version]:
				answers[versionName][int(item['id'])] = len(item['fixedFiles'])

		return answers

	def save_answers(self, _answers, _filename):
		from utils.PrettyStringBuilder import PrettyStringBuilder
		pretty = PrettyStringBuilder(_indent_depth=2)
		text = pretty.get_dicttext(_answers)
		f  = open(_filename, 'w')
		f.write(text)
		f.close()
		pass

	def merge(self, _group, _project, _bugs, _dups):
		merges = []
		bugID = 0
		for src, dup in _dups:
			if src not in _bugs or dup not in _bugs:
				print('passed %s\t%s\t%d\t%d' % (_group, _project, src, dup))
				continue
			bugID += 1
			bug = {}
			bug['id'] 			= str(bugID)
			bug['master'] 		= _bugs[src]['id']
			bug['duplicate'] 	= _bugs[dup]['id']
			bug['summary'] 		= _bugs[src]['summary'] + ' ' + _bugs[dup]['summary']
			bug['description'] 	= _bugs[src]['description'] + ' ' + _bugs[dup]['description']

			verSrc = _bugs[src]['version']
			verDup = _bugs[dup]['version']
			bug['version'] 		= verSrc if VersionUtil.cmpVersion(verSrc, verDup) > 0 else verDup

			verSrc = _bugs[src]['fixedVersion']
			verDup = _bugs[dup]['fixedVersion']
			bug['fixedVersion'] = verSrc if VersionUtil.cmpVersion(verSrc, verDup) > 0 else verDup

			bug['resolution'] 	= _bugs[src]['resolution']
			bug['opendate'] 	= min(_bugs[src]['opendate'], _bugs[dup]['opendate'])
			bug['fixdate'] 		= max(_bugs[src]['fixdate'], _bugs[dup]['fixdate'])
			bug['type'] 		= _bugs[src]['type']
			bug['fixedFiles']	= _bugs[src]['fixedFiles']
			bug['links'] 		= _bugs[src]['links'] + _bugs[dup]['links']

			merges.append(bug)
		return merges

	def load_bugs(self, _filename):
		bugs = {}
		text = open(_filename, 'r').read()
		doc = BeautifulSoup(text, 'html.parser')
		bugTags = doc.select('bugrepository > bug')

		for tag in bugTags:
			bug = {}
			info = tag.select('buginformation')[0]
			bug['id'] = tag.attrs['id']
			bug['summary'] = info.select('summary')[0].get_text()
			bug['description'] = info.select('description')[0].get_text()
			bug['type'] = info.select('type')[0].get_text()
			bug['version'] = info.select('version')[0].get_text()
			bug['fixedVersion'] = info.select('fixedversion')[0].get_text()
			bug['resolution'] = tag.attrs['resolution']
			bug['opendate'] = datetime.strptime(tag.attrs['opendate'], '%Y-%m-%d %H:%M:%S')
			bug['fixdate'] = datetime.strptime(tag.attrs['fixdate'], '%Y-%m-%d %H:%M:%S')

			bug['summary'] = cgi.html(re.sub(r'[^\x00-\x80]+', '', bug['summary']))  #re.sub(r'[^\w\s&\^\|/()\[\]\{\}<>+\-=*/`~!@#$%^,.:;\\\'"?]', '', bug['summary']))
			bug['description'] = BeautifulSoup(bug['description'], "html.parser").get_text()
			bug['description'] = cgi.html(re.sub(r'[^\x00-\x80]+', '', bug['description']))
			bug['description'] = cgi.html(re.sub(chr(27), '', bug['description']))

			bug['fixedFiles'] = []
			fixedFiles = tag.select('fixedfiles > file')
			for file in fixedFiles:
				bug['fixedFiles'].append({'type':file.attrs['type'], 'name':file.get_text()})

			bug['links'] = []
			links = tag.select('links > link')
			for link in links:
				bug['links'].append({'type': link.attrs['type'], 'description': link.attrs['description'], 'id':link.get_text()})

			bugs[int(bug['id'])] = bug
		return bugs

	def getItemsByVersion(self, _items, _versions):
		_versions = list(_versions)
		_versions.sort(key=cmp_to_key(VersionUtil.cmpVersion))
		version_bugs = dict((ver, list()) for ver in _versions)

		size = len(_versions)
		for idx in range(0, size):
			version = _versions[idx]
			nextVersion = _versions[idx + 1] if idx != size - 1 else '10000.0'  # assign big. version number

			for bugitem in _items:
				if VersionUtil.cmpVersion(version, bugitem['version']) > 0 and idx!=0: continue
				if VersionUtil.cmpVersion(bugitem['version'], nextVersion) >= 0: continue
				version_bugs[version].append(bugitem)

		vKeys = version_bugs.keys()
		for version in vKeys:
			if len(version_bugs[version]) != 0: continue
			del version_bugs[version]

		return version_bugs

	#######################################################################
	# Convert XML
	#######################################################################
	def convertText(self, _bug):
		'''
		Convert bug object to XML
		:param _bug:
		:return:
		'''
		format =  '\t<bug id="%s" master="%s" duplicate="%s" opendate="%s" fixdate="%s" resolution="%s">\n'
		format += '\t\t<buginformation>\n'
		format += '\t\t\t<summary>%s</summary>\n'
		format += '\t\t\t<description>%s</description>\n'
		format += '\t\t\t<version>%s</version>\n'
		format += '\t\t\t<fixedVersion>%s</fixedVersion>\n'
		format += '\t\t\t<type>%s</type>\n'
		format += '\t\t</buginformation>\n'
		format += '\t\t<fixedFiles>\n%s\n\t\t</fixedFiles>\n'
		format += '%s'  #this section for links
		format += '\t</bug>\n'

		fixedfiles = '\n'.join(
			'\t\t\t<file type="'+ f['type'] +'">' + f['name'] + '</file>'
			for f in _bug['fixedFiles']
		)

		links = '\n'.join(
			'\t\t\t<link type="'+ link['type']
			+ '" description="'+ link['description'] +'">'
			+ link['id'] + '</link>'
			for link in _bug['links']
		)
		if links !='':
			links = '\t\t<links>\n%s\n\t\t</links>\n'%links

		text = format% (_bug['id'],
						_bug['master'],
						_bug['duplicate'],
						_bug['opendate'].strftime('%Y-%m-%d %H:%M:%S'),
						_bug['fixdate'].strftime('%Y-%m-%d %H:%M:%S'),
						_bug['resolution'],
						_bug['summary'],
						_bug['description'],
						_bug['version'],
						_bug['fixedVersion'],
						_bug['type'],
						fixedfiles,
		                links)
		return text

	def outputXML(self, _project, _items, _targetPath):
		#write XML File
		output = codecs.open(_targetPath, 'w', 'utf-8')
		output.write('<?xml version = "1.0" encoding = "UTF-8" ?>\n<bugrepository name="%s">\n'%_project)
		for item in _items:
			output.write(self.convertText(item))
		output.write('</bugrepository>')
		output.flush()
		output.close()
		pass
