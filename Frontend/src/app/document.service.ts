import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { apiUrl } from './constantes/configs';

@Injectable({
  providedIn: 'root'
})
export class DocumentService {
  private apiUrl = apiUrl+'/process-document'; // Cambia a la URL correcta de tu back-end

  constructor(private http: HttpClient) {}

  // Método para enviar los datos del documento al backend
  uploadDocument(formData: FormData): Observable<any> {
    return this.http.post(this.apiUrl, formData);  // Enviar el formulario como FormData
  }
}