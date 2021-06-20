#-*- coding: utf-8 -*-

from utils.DiffTimer import DiffTimer


###############################################################################################################
class Progress(object):
	header = ''
	dot_point = 10
	line_point = 1000
	point = 0
	upper_bound = 0

	prev = 0
	percent_mode = False

	timer = None
	fulltimer = None

	def __init__(self, _header, _dot_point=0, _line_point=0, _percent_mode=False):
		self.reset(_header, _dot_point, _line_point, _percent_mode)

	def reset(self, _header, _dot_point=0, _line_point=0, _percent_mode=False):
		self.header = _header
		self.set_dotpoint(_dot_point)
		self.set_linepoint(_line_point)
		self.point = 0
		self.timer = DiffTimer()
		self.fulltimer = DiffTimer()
		self.prev = 1
		self.percent_mode = _percent_mode

	def set_header(self, _header):
		self.header = _header
		return self

	def set_upperbound(self, _max):
		self.upper_bound = _max
		return self

	def set_point(self, _point):
		self.point = _point
		return self

	def set_dotpoint(self, _dot_point):
		self.dot_point = _dot_point if _dot_point > 0 else 1
		return self

	def set_linepoint(self, _line_point):
		self.line_point = _line_point if _line_point > 0 else 1
		return self

	def start(self):
		print('%s'%self.header, end='')
		self.prev = 1
		self.timer.set()
		self.fulltimer.set()


	def _percent(self):

		div = int ((float(self.point) / self.upper_bound) * 100)
		if div >= 100: div=100

		for i in range(self.prev,div):
			if i==0: continue
			elif i%self.line_point==0: print(',', end='')
			elif i%self.dot_point==0:print('.', end='')

		self.prev = div

	def check(self, _msg=None):
		self.point += 1

		# work with percent
		if self.percent_mode is True:
			self._percent()
			return

		if (self.point % self.dot_point) == 0:
			print('.', end='')

		if (self.point % self.line_point) == 0:
			text = '%s'%('{:,}'.format(self.point))
			if self.upper_bound >0:
				text += '/%s'%('{:,}'.format(self.upper_bound))
			text += ' (time:%s'%self.timer.diff_auto()
			if _msg is not None:
				text += ' %s' %_msg
			text += ')'
			print(text)
			print('%s'%self.header, end='')

	def done(self, _msg=None):
		text = 'Done. (size:%s'%('{:,}'.format(self.point))
		text += ' time:%s'% self.fulltimer.diff_auto()
		if _msg is not None:
			text += ' %s)'%_msg
		else:
			text += ')'
		print(text)


