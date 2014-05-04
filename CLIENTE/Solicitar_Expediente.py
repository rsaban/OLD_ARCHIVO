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

class main:
	
	def __init__(self):
		#Obtenemos la ruta de la carpeta donde se encuentra el glade
		pathname = os.path.dirname(sys.argv[0])
		ruta = os.path.abspath(pathname) + "/UI/"
		pantallaPrincipal = ruta + "clienteArchivo.glade"
		
		builder= gtk.Builder()
		builder.add_from_file(pantallaPrincipal)

		self.rbPaMi = builder.get_object("rbPaMi")
		self.rbPaOtro = builder.get_object("rbPaOtro")
		self.tbPaOtro = builder.get_object("tbPaOtro")
		self.tbPaOtro.set_sensitive(False)
		self.tbExpdte = builder.get_object("tbExpdte")
		self.ckbtHoy = builder.get_object("ckbtHoy")
		self.tbCaja = builder.get_object("tbCaja")
		self.lbSolicitado = builder.get_object("lbSolicitado")

		self.lbSolicitado.set_visible(False)

		#Obtenemos el msgbox
		self.msgbox = builder.get_object("msgbox")
		self.lbMsgBox = builder.get_object("lbMsgBox")
		self.btAceptarMsgBox = builder.get_object("btAceptarMsgBox")


		dict = {"on_btSolicitar_clicked": self.btSolicitarClick,
				"on_btAceptarMsgBox_clicked": self.btAceptarMsgBoxClick,
				"on_rbPaOtro_clicked": self.rbPaOtroClick,
				"on_rbPaMi_clicked": self.rbPaMiClick,
				"on_msgbox_delete_event": self.msgboxDelete,
				"on_clienteArchivo_key_press_event": self.ReturnPulse,
				"gtk_main_quit": self.Salir
				}
		builder.connect_signals(dict)

	
	def btSolicitarClick(self, widget):
		
		expdte = self.tbExpdte.get_text()

		#if isinstance(expdte, int) == False:
		if expdte.isdigit() == False:
			self.msgbox.show()
			self.lbMsgBox.set_text("Con el número central es suficiente")
			self.btAceptarMsgBox.set_label("Intentaré Acordarme")
			return
		
		if len(expdte) < 6:
			self.msgbox.show()
			self.lbMsgBox.set_text("6 carácteres mínimo. Olvidate de cuentos, los ceros a la izquierda SI cuentan!!!")
			self.btAceptarMsgBox.set_label("Intentaré Acordarme")
			return

		if self.ckbtHoy.get_active() == True:
			necesitoHoy = "Sí"
		else:
			necesitoHoy = "No"

		caja = self.tbCaja.get_text()

		if caja == "" or caja.isspace() == True:
			self.msgbox.show()
			self.lbMsgBox.set_text("Échame un cable y escribe el número de caja, vale?. Si no lo sabes, escribe \"0\" y me doy por enterado :-)")
			self.btAceptarMsgBox.set_label("Voy a intentarlo")
			return


		if expdte == "" or expdte.isspace() == True:
			self.msgbox.show()
			self.lbMsgBox.set_text("Si no escribes el número de expediente, ¿cómo lo vas a solicitar, alma de cántaro?")
			self.btAceptarMsgBox.set_label("Intentaré Acordarme")
			return
		else:

			fechaPedido = datetime.date.today()
			
			try:
				c = MySQLdb.connect(*conexion.datos)
			except Exception, e:
				self.msgbox.show()
				self.lbMsgBox.set_text("No se pudo solicitar el expediente. El servidor no está disponible. Intentelo más tarde.")
				self.btAceptarMsgBox.set_label("Aceptar")
				return

		
			cursor = c.cursor()

			queryVerSiEstaPedido = "SELECT Solicitante FROM ExpedientesSolicitados WHERE Expdte = \'" + expdte + "'"

			try:
				cursor.execute(queryVerSiEstaPedido)
			except Exception, e:
				raise e

			estaPedido = cursor.fetchone()

			if estaPedido != None:
				self.msgbox.show()
				self.lbMsgBox.set_text("No puede solictar el expediente, ya ha sido solicitado por " + str(estaPedido[0]))
				self.btAceptarMsgBox.set_label("Aceptar")
		
			else:
				if self.rbPaMi.get_active() == True:
					solicitante = getpass.getuser()

					querySolicitar = "INSERT INTO ExpedientesSolicitados (Expdte, Solicitante, Fecha, NecesitoHoy, Caja) VALUES (\'" + expdte + "', '" + solicitante + "', '" + str(fechaPedido) + "', '" + necesitoHoy + "', '" + caja + "')"

					try:
						cursor.execute(querySolicitar)
						c.commit()
						self.lbSolicitado.set_visible(True)
						self.lbSolicitado.set_text("Último expediente solicitado: " + expdte)
						self.tbExpdte.set_text("")
						self.tbPaOtro.set_text("")
						self.tbCaja.set_text("")
						self.ckbtHoy.set_active(False)
						# self.msgbox.show()
						# self.lbMsgBox.set_text("Expediente Solicitado")
						# self.btAceptarMsgBox.set_label("Aceptar")
					except Exception, e:
						c.rollback()
						self.msgbox.show()
						self.lbMsgBox.set_text("No se pudo solicitar el expediente. Inténtelo más adelante.")
						self.btAceptarMsgBox.set_label("Aceptar")


				elif self.rbPaOtro.get_active() == True:

					solicitante = self.tbPaOtro.get_text()
							
					if solicitante == "" or solicitante.isspace() == True:
						self.msgbox.show()
						self.lbMsgBox.set_text("No soy adivino, dime a quién se lo llevo!!")
						self.btAceptarMsgBox.set_label("Siempre me pasa lo mismo!!")
						return
					else:
						
						if solicitante[0].isdigit() == True or solicitante[1].isdigit() == True or solicitante[2].isdigit() == True:
							self.msgbox.show()
							self.lbMsgBox.set_text("¿No habrás escrito el número de expediente en el cuadro que no toca, no?")
							self.btAceptarMsgBox.set_label("Siempre me pasa lo mismo!!")
							return
						else:
							solicitador = getpass.getuser()
							solicitante = solicitante + " (pedido por " + solicitador + ")"
							querySolicitar = "INSERT INTO ExpedientesSolicitados (Expdte, Solicitante, Fecha, NecesitoHoy, Caja) VALUES (\'" + expdte + "', '" + solicitante + "', '" + str(fechaPedido) + "', '" + necesitoHoy + "', '" + caja + "')"

							try:
								cursor.execute(querySolicitar)
								c.commit()
								self.lbSolicitado.set_visible(True)
								self.lbSolicitado.set_text("Último expediente solicitado: " + expdte)
								self.tbExpdte.set_text("")
								self.tbPaOtro.set_text("")
								self.tbCaja.set_text("")
								self.ckbtHoy.set_active(False)
								# self.msgbox.show()
								# self.lbMsgBox.set_text("Expediente Solicitado")
								# self.btAceptarMsgBox.set_label("Aceptar")
							except Exception, e:
								c.rollback()
								self.msgbox.show()
								self.lbMsgBox.set_text("No se pudo solicitar el expediente. Inténtelo más adelante.")
								self.btAceptarMsgBox.set_label("Aceptar")


			cursor.close()
			c.close()

	def rbPaOtroClick(self, widget):
		self.tbPaOtro.set_sensitive(True)

	def rbPaMiClick(self, widget):
		self.tbPaOtro.set_sensitive(False)
		self.tbPaOtro.set_text("")

	def ReturnPulse(self, widget, event):
		if event.keyval == gtk.keysyms.Return:
			self.btSolicitarClick(widget)

	def btAceptarMsgBoxClick(self, widget):
		
		if self.btAceptarMsgBox.get_label() == "Intentaré Acordarme" or self.btAceptarMsgBox.get_label() == "Voy a intentarlo" or self.btAceptarMsgBox.get_label() == "Siempre me pasa lo mismo!!":
			self.msgbox.hide()
		elif self.btAceptarMsgBox.get_label() == "Aceptar":
			self.msgbox.hide()
			self.tbExpdte.set_text("")
			self.tbPaOtro.set_text("")
			self.tbCaja.set_text("")
			self.ckbtHoy.set_active(False)

	def msgboxDelete(self, widget, data=None):
		self.msgbox.hide()
		return True

	def Salir(self, widget, data=None):
		gtk.main_quit()
		
		
if __name__=="__main__":
	
	main()
	gtk.main()