import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { SideapService } from './xxx.service';
import { UserService } from './user.service';
import { DocumentService } from './document.service';
import { HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterModule,
    CommonModule,HttpClientModule],  // Importar el RouterModule
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  providers: [SideapService,UserService,DocumentService],
})
export class AppComponent {
  title = 'chatbot';

  constructor(){
  }
}