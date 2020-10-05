export function getOffset(page: number, pageSize: number): number {
    return (page - 1) * pageSize;
}
