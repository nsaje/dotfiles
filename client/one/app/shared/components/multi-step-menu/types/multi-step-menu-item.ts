export interface MultiStepMenuItem {
    name: string;
    description?: string;
    handler: () => void;
    hasNextStep: boolean;
}
