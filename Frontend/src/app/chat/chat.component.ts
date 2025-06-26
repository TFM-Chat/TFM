import { Component, OnInit, ViewChild } from '@angular/core';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { apiUrl } from '../constantes/configs';
import { RecaptchaModule, RecaptchaComponent } from 'ng-recaptcha';



interface Documento {
  id: string;
  contenido: string;
  PDF: string;
  score: number;
  row_number: number;
  anio: number;
  titulo: string;
  desc: string;
  tem: string;
  subtema: string;
  expanded?: boolean;
}

interface ApiResponse {
  Documentos_recuperados: Documento[];
  Respuesta: string;
  Modelo_usado: string;
  Tiempo_consulta_modelo: number;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule, RecaptchaModule],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit {
  @ViewChild('captchaRef') recaptchaComponent: RecaptchaComponent | undefined;

  // En tu componente de Angular
  siteKey: string = 'XXXXXXXXXXXXXXXXXXX';  // Asegúrate de que tenga un valor por defecto o que sea inicializado correctamente
  question: string = '';
  response: string | null = null;
  documentos: Documento[] = [];
  loading: boolean = false;  // Manejo de la carga global
  loadingQuestion: boolean = false;  // Manejo de la carga específica de la consulta
  nombreUsuario: string = '';
  captchaToken: string | null = null;
  captchaError: string = '';  // Para mantener el mensaje de error

  constructor(private http: HttpClient, private router: Router) { }

  ngOnInit() {
    // Verificar si hay un usuario en sessionStorage
    this.nombreUsuario = sessionStorage.getItem('nombre') || 'Usuario';
  }

  // Enviar la pregunta y obtener la respuesta del chatbot
  sendQuestion() {
    // if (!this.captchaToken) {
    //   this.captchaError = 'Por favor, completa el reCAPTCHA.';
    //   return;
    // }

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

  // Método para cerrar sesión (logout)
  logout() {
    sessionStorage.clear();
    this.router.navigateByUrl('/login');
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