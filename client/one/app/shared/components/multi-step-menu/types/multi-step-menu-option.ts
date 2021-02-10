export interface MultiStepMenuOption {
    name: string;
    description?: string;
    nextOptions?: MultiStepMenuOption[];
    handler?: () => void;
}
