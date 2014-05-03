#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import pygtk
pygtk.require('2.0')
import gtk
import os
import sys
import datetime
import MySQLdb
import getpass
import conexion

from odf.opendocument import OpenDocumentSpreadsheet
from odf.style import Style, TextProperties, TableColumnProperties, Map
from odf.number import NumberStyle, CurrencyStyle, CurrencySymbol,  Number,  Text
from odf.text import P
from odf.table import Table, TableColumn, TableRow, TableCell

class main:
	
	def __init__(self):
		#Obtenemos la ruta de la carpeta donde se encuentra el glade
		pathname = os.path.dirname(sys.argv[0])
		ruta = os.path.abspath(pathname) + "/UI/"
		pantallaPrincipal = ruta + "servidorArchivo.glade"
		
		builder= gtk.Builder()
		builder.add_from_file(pantallaPrincipal)

		self.tbComentario = builder.get_object("tbComentario")
		self.tvSolicitudes = builder.get_object("tvSolicitudes")
		self.lstvSolicitudes = builder.get_object("lstvSolicitudes")
		self.rbCualquierDia = builder.get_object("rbCualquierDia")
		self.rbDiaSolicitud = builder.get_object("rbDiaSolicitud")
		self.calendar1 = builder.get_object("calendar1")


		#Obtenemos el msgbox
		self.msgbox = builder.get_object("msgbox")
		self.lbMsgBox = builder.get_object("lbMsgBox")
		self.btAceptarMsgBox = builder.get_object("btAceptarMsgBox")

		selection = self.tvSolicitudes.get_selection()
		selection.set_mode(gtk.SELECTION_MULTIPLE)

		#ponemos el calendario a fecha de hoy
		fechaHoy = datetime.date.today()
		ano = int(fechaHoy.strftime("%Y"))
		mes = int(fechaHoy.strftime("%m")) - 1
		dia = int(fechaHoy.strftime("%d"))
		self.calendar1.select_month(mes, ano)
		self.calendar1.select_day(dia)

		dict = {"on_btMostrarRegistros_clicked": self.btMostrarRegistrosClick,
				"on_btExportar_clicked": self.btExportarClick,
				"on_btEliminar_clicked": self.btEliminarClick,
				"on_btAceptarMsgBox_clicked": self.btAceptarMsgBoxClick,
				"on_msgbox_delete_event": self.MsgBoxDelete,
				"gtk_main_quit": self.Salir
				}
		builder.connect_signals(dict)


	# def Comentario(self, widget):
	# 	self.tbComentario.set_text("")


	def btMostrarRegistrosClick(self, widget):
		
		self.lstvSolicitudes.clear()

		try:
			c = MySQLdb.connect(*conexion.datos)
		except Exception, e:
			self.msgbox.show()
			self.lbMsgBox.set_text("No se puede conectar con la base de datos. Intentelo más tarde.")
			return

		cursor = c.cursor()

		if self.rbCualquierDia.get_active() == True:

			queryConsultaSolicitudes = "SELECT Fecha, Expdte, Caja, Solicitante, NecesitoHoy, Id FROM ExpedientesSolicitados ORDER BY Caja,cast(Expdte as unsigned) ASC"#, Caja ASC" 

			try:
				cursor.execute(queryConsultaSolicitudes)
			except Exception, e:
				raise e
			resultado = cursor.fetchall()

			for i in range(len(resultado)):
				self.lstvSolicitudes.append(resultado[i])

		elif self.rbDiaSolicitud.get_active() == True:

			ano, mes, dia = self.calendar1.get_date()
			fechaSolicitud = str(ano) + "-" + str(mes+1) + "-" + str(dia)

			queryConsultaSolicitudes = "SELECT Fecha, Expdte, Caja, Solicitante, NecesitoHoy,  Id FROM ExpedientesSolicitados WHERE Fecha = \'" + str(fechaSolicitud) + "' ORDER BY Caja,cast(Expdte as unsigned) ASC"#, Caja ASC" 

			try:
				cursor.execute(queryConsultaSolicitudes)
			except Exception, e:
				raise e
			resultado = cursor.fetchall()

			for i in range(len(resultado)):
				self.lstvSolicitudes.append(resultado[i])

		cursor.close()
		c.close()

	def btEliminarClick(self, widget):
		hoy = datetime.date.today()

		if self.tbComentario.get_text() == "Opcional: Introduzca comentario al eliminar" or self.tbComentario.get_text() == "" or self.tbComentario.get_text().isspace() == True:
			comentario = ""
		else:
			comentario = self.tbComentario.get_text()
		

		count = self.tvSolicitudes.get_selection().count_selected_rows()

		if count == 0:
			self.msgbox.show()
			self.lbMsgBox.set_text("¿Elijo yo por ti las filas que borro?")
			return

		for i in range(count):
		

			tree,iter = self.tvSolicitudes.get_selection().get_selected_rows()

			fecha = tree.get_value(tree.get_iter(iter[0]), 0)
			expediente = tree.get_value(tree.get_iter(iter[0]), 1)
			solicitado = tree.get_value(tree.get_iter(iter[0]), 3)
			idSolicitud = tree.get_value(tree.get_iter(iter[0]), 5)
			
			f = open("log.txt", "a")
			f.write ("Expediente " + expediente + ", solicitado por " + solicitado + " el " + fecha + ", entregado el " + str(hoy) + ". Comentario: " + comentario + "\n")
			f.close()
			
			try:
				c = MySQLdb.connect(*conexion.datos)
			except Exception, e:
				self.msgbox.show()
				self.lbMsgBox.set_text("El servidor no está disponible. Intentelo más tarde.")
				return
			#c = MySQLdb.connect(*conexion.datos)
			cursor = c.cursor()
			
			#borro de la base de datos
			queryBorrar = "DELETE FROM ExpedientesSolicitados WHERE Id = \'" + idSolicitud + "'"

			try:
				cursor.execute(queryBorrar)
				c.commit()
				#quito del treeview
				self.lstvSolicitudes.remove(tree.get_iter(iter[0]))
			except Exception, e:
				c.rollback()

		cursor.close()
		c.close()


	def btExportarClick(self, widget):
	
		count = self.tvSolicitudes.get_selection().count_selected_rows()

		#Exportamos todo el treeview si no se han seleccionado filas.
		if count == 0:
			self.tvSolicitudes.get_selection().select_all()

			tree,iter = self.tvSolicitudes.get_selection().get_selected_rows()
		
			textdoc = OpenDocumentSpreadsheet()
							
			# Start the table, and describe the columns
			table = Table(name="Solicitudes")
			
			for i in iter: #esto funciona aquí, porque no voy eliminando filas del treeview. Por eso en el botón eliminar tuve que hacerlo distinto.
				expediente = tree.get_value(tree.get_iter(i), 1)
				persona = tree.get_value(tree.get_iter(i), 3)
				fecha = tree.get_value(tree.get_iter(i), 0)
				caja = tree.get_value(tree.get_iter(i), 2)
				# Create a row (same as <tr> in HTML)
				tr = TableRow()
				table.addElement(tr)
				# Create a cell 
				cell = TableCell()
				cell.addElement(P(text=expediente)) # The current displayed value
				tr.addElement(cell)
				cell4 = TableCell()
				cell4.addElement(P(text=caja))
				tr.addElement(cell4)
				cell2 = TableCell()
				cell2.addElement(P(text=persona))
				tr.addElement(cell2)
				cell3 = TableCell()
				cell3.addElement(P(text=fecha))
				tr.addElement(cell3)

		#exportamos las filas seleccionadas
		else:

			tree,iter = self.tvSolicitudes.get_selection().get_selected_rows()
			# ret = []
			# for i in iter:
			# 	ret.append(tree.get_value(tree.get_iter(i), 0))

			textdoc = OpenDocumentSpreadsheet()
							
			# Start the table, and describe the columns
			table = Table(name="Solicitudes")
			
			for i in iter: #esto funciona aquí, porque no voy eliminando filas del treeview. Por eso en el botón eliminar tuve que hacerlo distinto.
				expediente = tree.get_value(tree.get_iter(i), 1)
				persona = tree.get_value(tree.get_iter(i), 3)
				fecha = tree.get_value(tree.get_iter(i), 0)
				caja = tree.get_value(tree.get_iter(i), 2)
				# Create a row (same as <tr> in HTML)
				tr = TableRow()
				table.addElement(tr)
				# Create a cell 
				cell = TableCell()
				cell.addElement(P(text=expediente)) # The current displayed value
				tr.addElement(cell)
				cell4 = TableCell()
				cell4.addElement(P(text=caja))
				tr.addElement(cell4)
				cell2 = TableCell()
				cell2.addElement(P(text=persona))
				tr.addElement(cell2)
				cell3 = TableCell()
				cell3.addElement(P(text=fecha))
				tr.addElement(cell3)

			
		textdoc.spreadsheet.addElement(table)
		textdoc.save("Solicitudes_de_Expediente.ods")

	
		if sys.platform == 'linux2':
			os.system("xdg-open Solicitudes_de_Expediente.ods &")
		else:
			os.system("start soffice --calc Solicitudes_de_Expediente.ods &")

		
	def btAceptarMsgBoxClick(self, widget):
		self.msgbox.hide()

	def MsgBoxDelete(self, widget, data=None):
		self.msgbox.hide()
		return True

	def Salir(self, widget, data=None):
		gtk.main_quit()

if __name__=="__main__":
	
	main()
	gtk.main()