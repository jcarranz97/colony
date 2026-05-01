"use client";
import { useState } from "react";
import { Formik } from "formik";
import {
  Button,
  Calendar,
  DateField,
  DatePicker,
  FieldError,
  Input,
  Label,
  ListBox,
  Modal,
  Select,
  Spinner,
  TextField,
} from "@heroui/react";
import { parseDate } from "@internationalized/date";
import type { DateValue } from "react-aria-components";
import { ExpenseTemplateCreateSchema } from "@/helpers/schemas";
import { RecurrenceConfigBuilder } from "./recurrence-config-builder";
import { addExpenseTemplate } from "./actions";
import type { ExpenseTemplate, PaymentMethod } from "@/helpers/types";

interface AddExpenseTemplateProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (template: ExpenseTemplate) => void;
  paymentMethods: PaymentMethod[];
}

const RECURRENCE_DEFAULT: Record<string, Record<string, unknown>> = {
  weekly: {},
  bi_weekly: { interval_days: 14 },
  monthly: {},
  custom: {},
};

export function AddExpenseTemplate({
  isOpen,
  onClose,
  onCreated,
  paymentMethods,
}: AddExpenseTemplateProps) {
  const [error, setError] = useState<string | null>(null);

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
              initialValues={{
                description: "",
                base_amount: "",
                currency: "",
                category: "",
                recurrence_type: "",
                recurrence_config: {} as Record<string, unknown>,
                reference_date: new Date().toISOString().split("T")[0],
                payment_method_id: "" as string,
              }}
              validationSchema={ExpenseTemplateCreateSchema}
              onSubmit={async (values, { setSubmitting, resetForm }) => {
                setError(null);
                const result = await addExpenseTemplate({
                  description: values.description,
                  base_amount: values.base_amount,
                  currency: values.currency as any,
                  category: values.category as any,
                  recurrence_type: values.recurrence_type as any,
                  recurrence_config: values.recurrence_config as any,
                  reference_date: values.reference_date,
                  payment_method_id: values.payment_method_id || null,
                });
                if (result.success) {
                  onCreated(result.data);
                  resetForm();
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
                    <Modal.Heading>Add Expense Template</Modal.Heading>
                  </Modal.Header>
                  <Modal.Body className="flex flex-col gap-4">
                    <TextField
                      isInvalid={!!errors.description && !!touched.description}
                      value={values.description}
                      onChange={(v) => setFieldValue("description", v)}
                    >
                      <Label>Name</Label>
                      <Input placeholder="e.g. Rent" />
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
                      <Input type="number" placeholder="0.00" />
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

                    <DatePicker
                      value={
                        values.reference_date
                          ? parseDate(values.reference_date)
                          : null
                      }
                      onChange={(date: DateValue | null) => {
                        if (date) {
                          const y = date.year;
                          const m = String(date.month).padStart(2, "0");
                          const d = String(date.day).padStart(2, "0");
                          setFieldValue("reference_date", `${y}-${m}-${d}`);
                        } else {
                          setFieldValue("reference_date", "");
                        }
                      }}
                      isInvalid={
                        !!errors.reference_date && !!touched.reference_date
                      }
                    >
                      <Label>Reference Date</Label>
                      <DateField.Group fullWidth>
                        <DateField.Input>
                          {(segment) => <DateField.Segment segment={segment} />}
                        </DateField.Input>
                        <DateField.Suffix>
                          <DatePicker.Trigger>
                            <DatePicker.TriggerIndicator />
                          </DatePicker.Trigger>
                        </DateField.Suffix>
                      </DateField.Group>
                      {touched.reference_date && errors.reference_date && (
                        <FieldError>{errors.reference_date}</FieldError>
                      )}
                      <DatePicker.Popover>
                        <Calendar aria-label="Reference date">
                          <Calendar.Header>
                            <Calendar.YearPickerTrigger>
                              <Calendar.YearPickerTriggerHeading />
                              <Calendar.YearPickerTriggerIndicator />
                            </Calendar.YearPickerTrigger>
                            <Calendar.NavButton slot="previous" />
                            <Calendar.NavButton slot="next" />
                          </Calendar.Header>
                          <Calendar.Grid>
                            <Calendar.GridHeader>
                              {(day) => (
                                <Calendar.HeaderCell>{day}</Calendar.HeaderCell>
                              )}
                            </Calendar.GridHeader>
                            <Calendar.GridBody>
                              {(date) => <Calendar.Cell date={date} />}
                            </Calendar.GridBody>
                          </Calendar.Grid>
                          <Calendar.YearPickerGrid>
                            <Calendar.YearPickerGridBody>
                              {({ year }) => (
                                <Calendar.YearPickerCell year={year} />
                              )}
                            </Calendar.YearPickerGridBody>
                          </Calendar.YearPickerGrid>
                        </Calendar>
                      </DatePicker.Popover>
                    </DatePicker>

                    <Select.Root
                      selectedKey={values.payment_method_id || null}
                      onSelectionChange={(key) =>
                        setFieldValue("payment_method_id", String(key))
                      }
                      isInvalid={
                        !!errors.payment_method_id &&
                        !!touched.payment_method_id
                      }
                      fullWidth
                    >
                      <Label>Payment Method</Label>
                      <Select.Trigger>
                        <Select.Value>
                          {({ isPlaceholder, selectedText }: any) =>
                            isPlaceholder ? (
                              <span className="text-default-400">
                                Select payment method...
                              </span>
                            ) : (
                              selectedText
                            )
                          }
                        </Select.Value>
                        <Select.Indicator />
                      </Select.Trigger>
                      {touched.payment_method_id &&
                        errors.payment_method_id && (
                          <p className="text-xs text-danger">
                            {errors.payment_method_id}
                          </p>
                        )}
                      <Select.Popover>
                        <ListBox>
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
                      {isSubmitting ? <Spinner size="sm" /> : "Add"}
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
