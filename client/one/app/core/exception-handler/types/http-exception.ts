export interface HttpException {
    message: string;
    errorCode: string;
    headers: (key: string) => string;
    status: number;
}