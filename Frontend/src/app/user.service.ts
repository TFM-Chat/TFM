import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private userSubject = new BehaviorSubject<string | null>(null);
  public user$ = this.userSubject.asObservable();

  setUser(name: string) {
    this.userSubject.next(name);
  }

  clearUser() {
    this.userSubject.next(null);
  }
}
