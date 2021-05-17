export interface Result {
  id: number;
  username: string;
  fullName: string;
  firstName: string;
  lastName: string;
  isStaff: boolean;
  email: string;
}

export interface UserSearch {
  count: number;
  next?: any;
  previous?: any;
  results: Result[];
}
