"use client";
import { useState } from "react";
import { Formik } from "formik";
import {
  Button,
  FieldError,
  Input,
  Label,
  ListBox,
  Modal,
  Select,
  Spinner,
  TextField,
} from "@heroui/react";
import { ExpenseTemplateSchema } from "@/helpers/schemas";
import { RecurrenceConfigBuilder } from "./recurrence-config-builder";
import { editExpenseTemplate } from "./actions";
import type { ExpenseTemplate, PaymentMethod } from "@/helpers/types";

interface EditExpenseTemplateProps {
  template: ExpenseTemplate | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdated: (template: ExpenseTemplate) => void;
  paymentMethods: PaymentMethod[];
}

const RECURRENCE_DEFAULT: Record<string, Record<string, unknown>> = {
  weekly: {},
  bi_weekly: { interval_days: 14 },
  monthly: {},
  custom: {},
};

export function EditExpenseTemplate({
  template,
  isOpen,
  onClose,
  onUpdated,
  paymentMethods,
}: EditExpenseTemplateProps) {
  const [error, setError] = useState<string | null>(null);

  if (!template) return null;

  return (
    <Modal.Root
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <Modal.Backdrop isDismissable>
        <Modal.Container>
          <Modal.Dialog>
            <Formik
              key={template.id}
              initialValues={{
                description: template.description,
                base_amount: template.base_amount,
                currency: template.currency,
                category: template.category,
                recurrence_type: template.recurrence_type,
                recurrence_config: template.recurrence_config as Record<
                  string,
                  unknown
                >,
                reference_date: template.reference_date,
                payment_method_id: template.payment_method?.id ?? null,
              }}
              validationSchema={ExpenseTemplateSchema}
              onSubmit={async (values, { setSubmitting }) => {
                setError(null);
                const result = await editExpenseTemplate(template.id, {
                  description: values.description,
                  base_amount: values.base_amount,
                  currency: values.currency as any,
                  category: values.category as any,
                  recurrence_type: values.recurrence_type as any,
                  recurrence_config: values.recurrence_config as any,
                  reference_date: values.reference_date,
                  payment_method_id: values.payment_method_id,
                });
                if (result.success) {
                  onUpdated(result.data);
                  onClose();
                } else {
                  setError(result.error.message);
                }
                setSubmitting(false);
              }}
            >
              {({
                values,
                errors,
                touched,
                setFieldValue,
                handleSubmit,
                isSubmitting,
              }) => (
                <form onSubmit={handleSubmit}>
                  <Modal.Header>
                    <Modal.Heading>Edit Expense Template</Modal.Heading>
                  </Modal.Header>
                  <Modal.Body className="flex flex-col gap-4">
                    <TextField
                      isInvalid={!!errors.description && !!touched.description}
                      value={values.description}
                      onChange={(v) => setFieldValue("description", v)}
                    >
                      <Label>Name</Label>
                      <Input />
                      {touched.description && errors.description && (
                        <FieldError>{errors.description}</FieldError>
                      )}
                    </TextField>

                    <TextField
                      isInvalid={!!errors.base_amount && !!touched.base_amount}
                      value={values.base_amount}
                      onChange={(v) => setFieldValue("base_amount", v)}
                    >
                      <Label>Amount</Label>
                      <Input type="number" />
                      {touched.base_amount && errors.base_amount && (
                        <FieldError>{errors.base_amount}</FieldError>
                      )}
                    </TextField>

                    <Select.Root
                      selectedKey={values.currency || null}
                      onSelectionChange={(key) =>
                        setFieldValue("currency", String(key))
                      }
                      isInvalid={!!errors.currency && !!touched.currency}
                      fullWidth
                    >
                      <Label>Currency</Label>
                      <Select.Trigger>
                        <Select.Value>
                          {({ isPlaceholder, selectedText }: any) =>
                            isPlaceholder ? (
                              <span className="text-default-400">
                                Select currency...
                              </span>
                            ) : (
                              selectedText
                            )
                          }
                        </Select.Value>
                        <Select.Indicator />
                      </Select.Trigger>
                      {touched.currency && errors.currency && (
                        <p className="text-xs text-danger">{errors.currency}</p>
                      )}
                      <Select.Popover>
                        <ListBox>
                          <ListBox.Item id="USD" textValue="USD">
                            USD
                          </ListBox.Item>
                          <ListBox.Item id="MXN" textValue="MXN">
                            MXN
                          </ListBox.Item>
                        </ListBox>
                      </Select.Popover>
                    </Select.Root>

                    <Select.Root
                      selectedKey={values.category || null}
                      onSelectionChange={(key) =>
                        setFieldValue("category", String(key))
                      }
                      isInvalid={!!errors.category && !!touched.category}
                      fullWidth
                    >
                      <Label>Category</Label>
                      <Select.Trigger>
                        <Select.Value>
                          {({ isPlaceholder, selectedText }: any) =>
                            isPlaceholder ? (
                              <span className="text-default-400">
                                Select category...
                              </span>
                            ) : (
                              selectedText
                            )
                          }
                        </Select.Value>
                        <Select.Indicator />
                      </Select.Trigger>
                      {touched.category && errors.category && (
                        <p className="text-xs text-danger">{errors.category}</p>
                      )}
                      <Select.Popover>
                        <ListBox>
                          <ListBox.Item id="fixed" textValue="Fixed">
                            Fixed
                          </ListBox.Item>
                          <ListBox.Item id="variable" textValue="Variable">
                            Variable
                          </ListBox.Item>
                        </ListBox>
                      </Select.Popover>
                    </Select.Root>

                    <Select.Root
                      selectedKey={values.recurrence_type || null}
                      onSelectionChange={(key) => {
                        const rt = String(key);
                        setFieldValue("recurrence_type", rt);
                        setFieldValue(
                          "recurrence_config",
                          RECURRENCE_DEFAULT[rt] ?? {},
                        );
                      }}
                      isInvalid={
                        !!errors.recurrence_type && !!touched.recurrence_type
                      }
                      fullWidth
                    >
                      <Label>Recurrence</Label>
                      <Select.Trigger>
                        <Select.Value>
                          {({ isPlaceholder, selectedText }: any) =>
                            isPlaceholder ? (
                              <span className="text-default-400">
                                Select recurrence...
                              </span>
                            ) : (
                              selectedText
                            )
                          }
                        </Select.Value>
                        <Select.Indicator />
                      </Select.Trigger>
                      {touched.recurrence_type && errors.recurrence_type && (
                        <p className="text-xs text-danger">
                          {errors.recurrence_type}
                        </p>
                      )}
                      <Select.Popover>
                        <ListBox>
                          <ListBox.Item id="weekly" textValue="Weekly">
                            Weekly
                          </ListBox.Item>
                          <ListBox.Item id="bi_weekly" textValue="Bi-weekly">
                            Bi-weekly
                          </ListBox.Item>
                          <ListBox.Item id="monthly" textValue="Monthly">
                            Monthly
                          </ListBox.Item>
                          <ListBox.Item id="custom" textValue="Custom">
                            Custom
                          </ListBox.Item>
                        </ListBox>
                      </Select.Popover>
                    </Select.Root>

                    {values.recurrence_type && <RecurrenceConfigBuilder />}

                    <TextField
                      isInvalid={
                        !!errors.reference_date && !!touched.reference_date
                      }
                      value={values.reference_date}
                      onChange={(v) => setFieldValue("reference_date", v)}
                    >
                      <Label>Reference Date</Label>
                      <Input type="date" />
                      {touched.reference_date && errors.reference_date && (
                        <FieldError>{errors.reference_date}</FieldError>
                      )}
                    </TextField>

                    <Select.Root
                      selectedKey={values.payment_method_id ?? "none"}
                      onSelectionChange={(key) =>
                        setFieldValue(
                          "payment_method_id",
                          key === "none" ? null : String(key),
                        )
                      }
                      fullWidth
                    >
                      <Label>Payment Method (optional)</Label>
                      <Select.Trigger>
                        <Select.Value>
                          {({ isPlaceholder, selectedText }: any) =>
                            isPlaceholder ? (
                              <span className="text-default-400">None</span>
                            ) : (
                              selectedText
                            )
                          }
                        </Select.Value>
                        <Select.Indicator />
                      </Select.Trigger>
                      <Select.Popover>
                        <ListBox>
                          <ListBox.Item id="none" textValue="None">
                            None
                          </ListBox.Item>
                          {paymentMethods
                            .filter((m) => m.active)
                            .map((m) => (
                              <ListBox.Item
                                key={m.id}
                                id={m.id}
                                textValue={m.name}
                              >
                                {m.name}
                              </ListBox.Item>
                            ))}
                        </ListBox>
                      </Select.Popover>
                    </Select.Root>

                    {error && <p className="text-sm text-danger">{error}</p>}
                  </Modal.Body>
                  <Modal.Footer className="gap-2">
                    <Button variant="ghost" onPress={onClose}>
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      variant="primary"
                      isDisabled={isSubmitting}
                    >
                      {isSubmitting ? <Spinner size="sm" /> : "Save"}
                    </Button>
                  </Modal.Footer>
                </form>
              )}
            </Formik>
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
    </Modal.Root>
  );
}
