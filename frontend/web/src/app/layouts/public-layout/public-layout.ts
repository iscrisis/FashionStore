import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { PublicHeader } from './public-header/public-header';

@Component({
  selector: 'app-public-layout',
  imports: [RouterOutlet, PublicHeader],
  templateUrl: './public-layout.html',
  styleUrl: './public-layout.scss',
})
export class PublicLayout {}
