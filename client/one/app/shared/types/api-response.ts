export interface ApiResponse<T1, T2 = null> {
    data: T1;
    extra?: T2;
    count?: number;
    next?: string | null;
    previous?: string | null;
}
