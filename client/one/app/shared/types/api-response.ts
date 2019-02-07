export interface ApiResponse<T1, T2 = null> {
    data: T1;
    extra: T2;
}
