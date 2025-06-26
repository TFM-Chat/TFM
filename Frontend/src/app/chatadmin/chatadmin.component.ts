import { Component, OnInit, ViewChild } from '@angular/core';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { apiUrl, apiUrlAnonimizar } from '../constantes/configs';
import { DocumentService } from '../document.service';
import { RecaptchaModule,RecaptchaComponent } from 'ng-recaptcha';

import { TabsModule } from 'ngx-bootstrap/tabs';

interface Documento {
  id: string;
  contenido: string;
  PDF: string;
  score: number;
  timestamp: number;
  row_number: number;  // Número de fila
  anio: number;        // Año del documento
  titulo: string;      // Título del documento
  desc: string;        // Descripción del documento
  tem: string;        // Tema del documento
  subtema: string;     // Subtema del documento
  borrado: boolean;    // Indica si el documento ha sido borrado
  expanded?: boolean;  // Propiedad opcional para manejar la expansión del contenido
}

interface DocumentoCosmos {
  borrado: boolean;    // Indica si el documento está marcado como borrado
  id: string;          // ID del documento
  url: string;         // URL del documento (PDF o enlace relacionado)
  row_number: string;  // Número de fila del documento
  anio: number;        // Año del documento
  titulo: string;      // Título del documento
  desc: string;        // Descripción del documento
  tema: string;        // Tema del documento
  subtema: string;     // Subtema relacionado con el documento
}

interface ApiResponse {
  Documentos_recuperados: Documento[];
  Pregunta: string;
  Respuesta: string;
  Modelo_usado: string;
  Tiempo_consulta_modelo: number;
  Tiempo_embeddings: number;
  Tokens_documentos: number;
  Tokens_pregunta: number;
  Tokens_respuesta: number;
}

@Component({
  selector: 'app-chat-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule, ReactiveFormsModule, TabsModule,RecaptchaModule],
  templateUrl: './chatadmin.component.html',
  styleUrls: ['./chatadmin.component.css']
})


export class ChatAdminComponent implements OnInit {
  @ViewChild('captchaRef') recaptchaComponent: RecaptchaComponent | undefined;
  question: string = '';
  response: string | null = null;
  documentos: Documento[] = [];
  technicalDataVisible: boolean = false;  // variable para controlar la visibilidad de los datos técnicos
  technicalData: Partial<ApiResponse> = {};  // datos técnicos del modelo
  loading: boolean = false;  // variable para el estado de carga

  documentosBorrados: DocumentoCosmos[] = [];
  documentosNoBorrados: DocumentoCosmos[] = [];
  documentosBorradosFiltrados: DocumentoCosmos[] = [];
  documentosNoBorradosFiltrados: DocumentoCosmos[] = [];
  siteKey: string = 'xxxxxxxxxxxxxxxx';  // Asegúrate de que tenga un valor por defecto o que sea inicializado correctamente
  captchaToken: string | null = null;
  captchaError: string = '';  // Para mantener el mensaje de error

  filtroBorrados: string = '';
  filtroNoBorrados: string = '';
  loadingQuestion: boolean = false;
  // Paginación
  currentPageBorrados: number = 1;
  currentPageNoBorrados: number = 1;
  documentsPerPage: number = 4;  // Número de documentos por página
  pagesPerView: number = 10;     // Número de páginas que se mostrarán en cada vista de paginación
  pageViewStart: number = 1;     // Inicio del rango de páginas mostradas
  totalPagesBorrados: number = 0;
  totalPagesNoBorrados: number = 0;

  esAnonimo: boolean = false;  // Variable para verificar si el usuario es anónimo
  nombreUsuario: string = '';  // Variable para almacenar el nombre del usuario
  infoUsuario: string = ''

  razonAccion: string = '';  // Variable para almacenar la razón de la acción
  isReasonModalOpen: boolean = false;  // Controla la visibilidad del modal
  tipoAccion: string = '';  // Variable para distinguir si es eliminar o restaurar
  documentoSeleccionado: any;  // Documento seleccionado para eliminar/restaurar
  uploadForm: FormGroup;
  selectedFile: File | null = null;
  loadingFile: boolean = false;  // Controla el estado de carga
  errorMessage: string | null = null;

  isUploadModalOpen: boolean = false;  // Controla la visibilidad del modal de carga de documento

  loadingFileManagement: boolean = false;
  successMessageFileManagement: string = '';
  errorMessageManagement: string = '';


  constructor(private fb: FormBuilder,
    private http: HttpClient,
    private router: Router, private documentService: DocumentService) {
    this.uploadForm = this.fb.group({
      titulo: ['', Validators.required],
      descripcion: ['', Validators.required],
      tema: ['', Validators.required],
      subtema: ['', Validators.required],
      fecha: ['', Validators.required],
      pdf: [null, Validators.required]
    });

  }
  
  isModalOpen = false;
  selectedDoc: any = {};
  ngOnInit() {
    // Verificar si hay un usuario en sessionStorage

    // Si no hay nombre en sessionStorage, redirigir a la página de login
    if (!sessionStorage.getItem('nombre')) {
      this.logout()
    }
    this.nombreUsuario = sessionStorage.getItem('nombre') || 'Usuario';
    const rol = sessionStorage.getItem('rol') || 'anonimo';  // Si no hay rol, considerar como anónimo
    this.esAnonimo = rol === 'anonimo';  // Verificar si el rol es anónimo
    if (!this.esAnonimo) this.fetchDocuments(false, '');
    this.infoUsuario = sessionStorage.getItem('identificacion') + "||" + sessionStorage.getItem('nombre') + "||" + sessionStorage.getItem('idPersona')
  }


  // Método para abrir el modal de carga de documento
  abrirModalUpload() {
    this.isUploadModalOpen = true;
  }

  // Método para cerrar el modal de carga de documento
  cerrarModalUpload() {
    this.isUploadModalOpen = false;
  }



  abrirModal(doc: any) {
    this.selectedDoc = doc;
    this.isModalOpen = true;
  }

  cerrarModal() {
    this.isModalOpen = false;
    this.selectedDoc = {};
  }




  sendQuestion() {
    if (!this.captchaToken) {
      this.captchaError = 'Por favor, completa el reCAPTCHA.';
      return;
    }

    this.loadingQuestion = true;
    const url = apiUrl + '/query';
    const payload = { question: this.question, recaptchaToken: this.captchaToken };

    this.http.post<ApiResponse>(url, payload).subscribe(
      (data) => {
        this.response = data.Respuesta;
        this.documentos = data.Documentos_recuperados;
        this.loadingQuestion = false;
        this.resetCaptcha(); // Restablecer el captcha después de la consulta
      },
      (error) => {
        console.error('Error:', error);
        this.response = 'Hubo un error al procesar tu solicitud.';
        this.loadingQuestion = false;
        this.resetCaptcha(); // Restablecer el captcha después de un error
      }
    );
  }
  resetComponentquestion() {
    this.question = '';      // Reiniciar campos del formulario o variables
    this.response = null;     // Reiniciar la respuesta
    this.documentos = [];     // Limpiar la lista de documentos
    this.technicalDataVisible = false;  // Reiniciar otras variables necesarias
    this.loading = false;     // Detener cualquier indicador de carga
    this.loadingQuestion = false; // Resetear indicador de carga de la pregunta
  }

  toggleTechnicalData() {
    this.technicalDataVisible = !this.technicalDataVisible;
  }

  downloadLog() {
    const url = 'https://chat/download-log';
    const payload = { key: 'PRUEBALOG' };  // Replace 'PRUEBALOG' with your actual key

    this.http.post(url, payload, { responseType: 'blob' }).subscribe(
      (blob) => {
        const a = document.createElement('a');
        const objectUrl = URL.createObjectURL(blob);
        a.href = objectUrl;
        a.download = 'application.log';
        a.click();
        URL.revokeObjectURL(objectUrl);
      },
      (error) => {
        console.error('Error downloading log file:', error);
      }
    );
  }
  fetchDocuments(withAlert: boolean, mensaje: string) {
    this.loading = true;
    const url = `${apiUrl}/all-documents`;

    this.http.get<DocumentoCosmos[]>(url).subscribe(
      (data) => {
        // Filtrar documentos borrados
        this.documentosBorrados = data.filter(doc => doc.borrado === true);
        this.documentosBorradosFiltrados = this.documentosBorrados;
        this.totalPagesBorrados = this.getTotalPagesBorrados();

        // Filtrar documentos no borrados
        this.documentosNoBorrados = data.filter(doc => doc.borrado === false);
        this.documentosNoBorradosFiltrados = this.documentosNoBorrados;
        this.totalPagesNoBorrados = this.getTotalPagesNoBorrados();
        this.loading = false;  // Termina la carga de documentos
        if (withAlert) {
          alert(mensaje)
          this.resetComponentquestion()

        }
      },
      (error) => {
        console.error('Error fetching documents:', error);
        if (withAlert) {
          alert('Error fetching documents')
        }
        this.loading = false;  // Termina la carga de documentos con error
      }
    );
  }

  // Filtrar documentos borrados
  filtrarBorrados() {
    this.documentosBorradosFiltrados = this.documentosBorrados.filter(doc =>
      (doc.url && doc.url.toLowerCase().includes(this.filtroBorrados.toLowerCase())) ||
      (doc.titulo && doc.titulo.toLowerCase().includes(this.filtroBorrados.toLowerCase())) ||
      (doc.desc && doc.desc.toLowerCase().includes(this.filtroBorrados.toLowerCase())) ||
      (doc.tema && doc.tema.toLowerCase().includes(this.filtroBorrados.toLowerCase())) ||
      (doc.subtema && doc.subtema.toLowerCase().includes(this.filtroBorrados.toLowerCase())) ||
      (doc.anio && doc.anio.toString().includes(this.filtroBorrados))
    );
  }

  // Filtrar documentos no borrados
  filtrarNoBorrados() {
    this.documentosNoBorradosFiltrados = this.documentosNoBorrados.filter(doc =>
      (doc.url && doc.url.toLowerCase().includes(this.filtroNoBorrados.toLowerCase())) ||
      (doc.titulo && doc.titulo.toLowerCase().includes(this.filtroNoBorrados.toLowerCase())) ||
      (doc.desc && doc.desc.toLowerCase().includes(this.filtroNoBorrados.toLowerCase())) ||
      (doc.tema && doc.tema.toLowerCase().includes(this.filtroNoBorrados.toLowerCase())) ||
      (doc.subtema && doc.subtema.toLowerCase().includes(this.filtroNoBorrados.toLowerCase())) ||
      (doc.anio && doc.anio.toString().includes(this.filtroNoBorrados))
    );
  }


  // Función para obtener la paginación actualizada para la vista de paginación
  getPaginatedPages(totalPages: number): number[] {
    const endPage = Math.min(this.pageViewStart + this.pagesPerView - 1, totalPages);
    const pages: number[] = [];
    for (let i = this.pageViewStart; i <= endPage; i++) {
      pages.push(i);
    }
    return pages;
  }

  // Cambio de rango de páginas
  changePageRange(next: boolean, totalPages: number) {
    if (next) {
      this.pageViewStart = Math.min(this.pageViewStart + this.pagesPerView, totalPages);
    } else {
      this.pageViewStart = Math.max(this.pageViewStart - this.pagesPerView, 1);
    }
  }

  // Paginación de documentos borrados
  getPaginatedBorrados(): DocumentoCosmos[] {
    const startIndex = (this.currentPageBorrados - 1) * this.documentsPerPage;
    const endIndex = startIndex + this.documentsPerPage;
    return this.documentosBorradosFiltrados.slice(startIndex, endIndex);
  }

  // Total de páginas para documentos borrados
  getTotalPagesBorrados(): number {
    return Math.ceil(this.documentosBorradosFiltrados.length / this.documentsPerPage);
  }

  // Función para cambiar la página actual
  changePageBorrados(page: number) {
    if (page > 0 && page <= this.totalPagesBorrados) {
      this.currentPageBorrados = page;
    }
  }



  // Paginación de documentos no borrados
  getPaginatedNoBorrados(): DocumentoCosmos[] {
    const startIndex = (this.currentPageNoBorrados - 1) * this.documentsPerPage;
    const endIndex = startIndex + this.documentsPerPage;
    return this.documentosNoBorradosFiltrados.slice(startIndex, endIndex);
  }

  // Total de páginas para documentos no borrados
  getTotalPagesNoBorrados(): number {
    return Math.ceil(this.documentosNoBorradosFiltrados.length / this.documentsPerPage);
  }

  // Función para cambiar la página actual
  changePageNoBorrados(page: number) {
    if (page > 0 && page <= this.totalPagesNoBorrados) {
      this.currentPageNoBorrados = page;
    }
  }




  // Función general para actualizar el estado del documento (eliminar/restaurar)
  actualizarDocumento(row_number: any, tipoUpdate: boolean, mensajeExito: string, infoUsuario: string, razonAccion: string) {

    this.loading = true;  // Activar el indicador de carga

    // Enviar los datos por el body en la petición PUT
    const body = {
      row_number: row_number,
      tipo: tipoUpdate,
      infoUsuario: infoUsuario,
      razonAccion: razonAccion
    };
    console.log('body', body)
    this.http.put(`${apiUrl}/updatedocument`, body).subscribe(() => {
      this.loading = false;  // Desactivar el indicador de carga

      this.loading = true;
      this.fetchDocuments(true, mensajeExito)
    }, (error) => {
      console.error('Error al actualizar el documento:', error);
      this.loading = false;  // Desactivar el indicador de carga en caso de error
      alert('Hubo un error al actualizar el documento');
    });

  }

  abrirModalRazon(documento: any, tipo: string) {
    this.documentoSeleccionado = documento;
    this.tipoAccion = tipo;
    this.isReasonModalOpen = true;  // Abrir el modal
  }

  cerrarModalRazon() {
    this.isReasonModalOpen = false;  // Cerrar el modal
    this.razonAccion = '';  // Limpiar la razón
  }

  confirmarAccion() {
    if (this.razonAccion.trim() === '') {
      alert('Por favor ingrese un motivo para ' + this.tipoAccion);
      return;
    }

    const row_number = this.documentoSeleccionado.row_number;
    if (this.tipoAccion === 'eliminar') {
      this.actualizarDocumento(row_number, true, 'Documento eliminado exitosamente', this.infoUsuario, this.tipoAccion + ":" + this.razonAccion);
    } else if (this.tipoAccion === 'restaurar') {
      this.actualizarDocumento(row_number, false, 'Documento restaurado exitosamente', this.infoUsuario, this.tipoAccion + ":" + this.razonAccion);
    }
    this.cerrarModalRazon();
  }

  // Abrir el modal de confirmación para eliminar
  eliminarDocumento(documento: any) {
    if (!this.esAnonimo) {
      this.abrirModalRazon(documento, 'eliminar');
    }
  }

  // Abrir el modal de confirmación para restaurar
  restaurarDocumento(documento: any) {
    if (!this.esAnonimo) {
      this.abrirModalRazon(documento, 'restaurar');
    }
  }

  // Método para cerrar sesión (logout)
  logout() {
    sessionStorage.clear();  // Borrar todos los datos del sessionStorage
    this.router.navigateByUrl('/login');  // Redirigir a la pantalla de login
  }



  // Manejar el cambio de archivo (PDF)
  onFileChange(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.uploadForm.patchValue({
        pdf: file
      });
      this.uploadForm.get('pdf')?.updateValueAndValidity();
      this.errorMessage = '';
    } else {
      this.uploadForm.patchValue({
        pdf: null
      });
      this.errorMessage = 'No se seleccionó ningún archivo.';
    }
  }

  abrirHerramientaAnonimizar() {
    window.open(apiUrlAnonimizar, '_blank');
  }

  // Método para enviar el formulario
  // Enviar los datos al backend
  onSubmit() {
    if (this.uploadForm.valid) {
      this.loadingFileManagement = true;  // Mostrar el estado de carga
      this.errorMessageManagement = '';  // Limpiar cualquier mensaje de error previo
      this.successMessageFileManagement = '';  // Limpiar cualquier mensaje de éxito previo
  
      const formData = new FormData();
      formData.append('titulo', this.uploadForm.get('titulo')?.value);
      formData.append('descripcion', this.uploadForm.get('descripcion')?.value);
      formData.append('tema', this.uploadForm.get('tema')?.value);
      formData.append('subtema', this.uploadForm.get('subtema')?.value);
      formData.append('fecha', this.uploadForm.get('fecha')?.value);
      formData.append('file', this.uploadForm.get('pdf')?.value);
  
      // Usar el servicio para enviar los datos al backend
      this.documentService.uploadDocument(formData).subscribe(
        (response) => {
          console.log('Documento subido con éxito:', response);
          this.loadingFileManagement = false;  // Ocultar el estado de carga
          this.successMessageFileManagement = 'Documento subido con éxito';  // Mostrar el mensaje de éxito
          this.fetchDocuments(true, 'Documento creado exitosamente')
          this.cerrarModalUpload();  // Cerrar el modal al completar
        },
        (error) => {
          console.error('Error al subir el documento:', error);
          this.loadingFileManagement = false;  // Ocultar el estado de carga en caso de error
          
          // Obtener el mensaje de error del backend si está disponible
          const errorMsg = error.error?.error || 'Ocurrió un error desconocido al subir el documento.';
          
          this.errorMessageManagement = `Ocurrió un error al subir el documento. Por favor, intente nuevamente. Error: ${errorMsg}`;
          this.cerrarModalUpload();  // Cerrar el modal al completar
        }
      );
    }
  }

  resolvedCaptcha(token: string | null): void {
    this.captchaToken = token;
    if (!token) {
      this.captchaError = '';
    } else {
      this.captchaError = '';  // Limpiar mensaje de error cuando se resuelve el captcha
    }
  }

  resetCaptcha(): void {
    this.captchaToken = null; // Limpiar el token del captcha
    if (this.recaptchaComponent) {
      this.recaptchaComponent.reset(); // Reinicia el reCAPTCHA
    }
  }


}