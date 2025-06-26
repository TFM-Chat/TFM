import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { UserService } from '../user.service';  // Importar el nuevo servicio
import { SideapService } from '../xxxx..service';
import { HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
  standalone: true,
  imports: [ReactiveFormsModule, CommonModule, HttpClientModule],
  providers: [SideapService]
})
export class LoginComponent {
  formulario: FormGroup;
  errorMessage: string | null = null;
  loading: boolean = false;  // Variable para controlar el estado de carga

  constructor(
    private fb: FormBuilder,
    private serviceSideap: SideapService,
    private userService: UserService,
    private router: Router
  ) {
    this.formulario = this.fb.group({
      correo: ['', [Validators.required, Validators.email]],
      contrasenia: ['', Validators.required],
      anonimo: [false]
    });

    this.formulario.get('anonimo')?.valueChanges.subscribe((anonimo: boolean) => {
      console.log('Anonimo value changed:', anonimo);  // Log para cambios en el checkbox
      if (anonimo) {
        this.formulario.get('correo')?.disable();
        this.formulario.get('contrasenia')?.disable();
      } else {
        this.formulario.get('correo')?.enable();
        this.formulario.get('contrasenia')?.enable();
      }
    });
  }

  login() {
    console.log('Login initiated');  // Log al iniciar el login
    this.errorMessage = null;
    this.loading = true;  // Activar el indicador de carga
    console.log('Formulario:', this.formulario.value);  // Log para ver el contenido del formulario

    const esAnonimo = this.formulario.controls['anonimo'].value;

    if (esAnonimo) {
      console.log('Usuario anónimo, redirigiendo a /chat');
      sessionStorage.setItem('rol', 'anonimo');
      sessionStorage.setItem('nombre', 'Usuario Anónimo');
      this.userService.setUser('Usuario Anónimo');
      this.loading = false;
      this.router.navigateByUrl('/chat');
    } else {
      const nombreUsuario = this.formulario.controls['correo'].value;
      const contrasenia = this.formulario.controls['contrasenia'].value;

      console.log('Autenticando con correo:', nombreUsuario);  // Log para el email ingresado

      this.serviceSideap.login(nombreUsuario, contrasenia).subscribe(
        (res) => {
          console.log('Respuesta de login:', res);  // Log para la respuesta del servicio de login
          if (res.codigo === 1) {
            const documento = res.response.prsPersona.numeroDocumento;
            console.log('Usuario autenticado, obteniendo información con documento:', documento);

            this.serviceSideap.getUser(documento).subscribe(
              (resp) => {
                console.log('Información del usuario obtenida:', resp);  // Log para la respuesta del servicio getUser

                this.serviceSideap.verificarEditor(documento).subscribe(
                  (verificacion) => {
                    console.log('Verificación de rol de editor:', verificacion);  // Log para la verificación del rol de editor
                    this.storeUserInfo(res, resp, verificacion);
                    this.loading = false;
                    this.router.navigateByUrl('/chat');
                  },
                  (error) => {
                    console.error('Error en verificarEditor:', error.message);  // Log en caso de error
                    this.errorMessage = error.message;
                    this.loading = false;
                  }
                );
              },
              (error) => {
                console.error('Error al obtener información del usuario:', error.message);  // Log en caso de error en getUser
                this.errorMessage = error.message;
                this.loading = false;
              }
            );
          } else {
            console.log('Error de autenticación:', res.mensaje);  // Log para errores de autenticación
            this.errorMessage = res.mensaje;
            this.loading = false;
          }
        },
        (error) => {
          console.error('Error en la solicitud de login:', error);  // Log para errores en la solicitud HTTP
          this.errorMessage = error.message;
          this.loading = false;
        }
      );
    }
  }

  storeUserInfo(res: any, resp: any, verificacion: any) {
    console.log('Almacenando información del usuario en sessionStorage');  // Log cuando se almacena la información del usuario
    sessionStorage.setItem('identificacion', res.response.prsPersona.numeroDocumento);
    sessionStorage.setItem('nombre', res.response.prsPersona.nombre);
    sessionStorage.setItem('idPersona', resp.Persona[0].IdPersona);
    sessionStorage.setItem('codigoCargo', resp.Persona[0].CodigoCargo);
    sessionStorage.setItem('cargo', resp.Persona[0].Cargo);
    sessionStorage.setItem('dependencia', resp.Persona[0].Dependencia);
    sessionStorage.setItem('dependenciaId', resp.Persona[0].IdDependencia);
    sessionStorage.setItem('jefe', resp.Persona[0].NumeroDocumentoJefe);
    
    const nombre = res.response.prsPersona.nombre;
    console.log('Nombre del usuario:', nombre);  // Log del nombre del usuario

    if (verificacion.esEditor) {
      sessionStorage.setItem('rol', 'editor');
      console.log('El usuario es editor');
    } else {
      sessionStorage.setItem('rol', 'lector');
      console.log('El usuario es lector');
    }

    this.userService.setUser(nombre);
  }
}