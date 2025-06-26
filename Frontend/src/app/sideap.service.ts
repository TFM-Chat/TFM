import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import {apiUrl} from '../app/constantes/configs'


@Injectable({
  providedIn: 'root'
})
export class SideapService {

  private loginUrl = apiUrl+'/login';  // Actualiza la URL según corresponda
  private obtenerDatosBasicosPersonaUrl = apiUrl+'/obtenerDatosBasicosPersona';  // Actualiza la URL según corresponda
  private verificarEditorUrl = apiUrl + '/verificarEditor';  // URL para verificar si el usuario es Editor


  constructor(private http: HttpClient) { }

  login(nombreUsuario: string, contrasenia: string): Observable<any> {
    const headers = new HttpHeaders().set('Content-Type', 'application/json');
    const body = { nombreUsuario, contrasenia };
    return this.http.post(this.loginUrl, body, { headers });
  }

  getUser(documento: string): Observable<any> {
    const headers = new HttpHeaders().set('Content-Type', 'application/json');
    return this.http.get(`${this.obtenerDatosBasicosPersonaUrl}?documento=${documento}`, { headers });
  }
  verificarEditor(cedula: string): Observable<any> {
    const headers = new HttpHeaders().set('Content-Type', 'application/json');
    return this.http.get(`${this.verificarEditorUrl}?cedula=${cedula}`, { headers });
  }
}