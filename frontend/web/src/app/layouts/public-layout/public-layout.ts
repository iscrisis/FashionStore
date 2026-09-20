import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AsistenteIa } from '../../features/cliente/asistente-ia/asistente-ia';
import { PublicHeader } from './public-header/public-header';

@Component({
  selector: 'app-public-layout',
  imports: [RouterOutlet, PublicHeader, AsistenteIa],
  templateUrl: './public-layout.html',
  styleUrl: './public-layout.scss',
})
export class PublicLayout {}
