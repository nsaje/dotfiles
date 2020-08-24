export abstract class ConnectionRowParentComponent<T> {
    abstract onRemoveConnection(connection: T): any;
    abstract isConnectionReadonly(connection: T): boolean;
}
